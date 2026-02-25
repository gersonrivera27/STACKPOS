using Blazored.LocalStorage;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using BurgerPOS.Models;

namespace BurgerPOS.Services;

/// <summary>
/// DelegatingHandler que inyecta automáticamente el JWT token en las requests
/// </summary>
public class JwtAuthorizationMessageHandler : DelegatingHandler
{
    private readonly AuthStateProvider _authStateProvider;

    public JwtAuthorizationMessageHandler(AuthStateProvider authStateProvider)
    {
        _authStateProvider = authStateProvider;
    }

    protected override async Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request, 
        CancellationToken cancellationToken)
    {
        try
        {
            // Obtener token del AuthStateProvider (maneja reintentos seguros)
            var token = await _authStateProvider.GetToken();
            
            if (!string.IsNullOrWhiteSpace(token))
            {
                // Agregar header Authorization: Bearer {token}
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            }
        }
        catch (InvalidOperationException)
        {
            // Ignorar error si JS Interop no está disponible (ej. pre-rendering)
            // La request se enviará sin token, lo que podría causar un 401,
            // pero evita que la aplicación crashee.
        }

        var response = await base.SendAsync(request, cancellationToken);

        if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
        {
            // Intentar refrescar el token
            try
            {
                var refreshToken = await _authStateProvider.GetRefreshToken();
                if (!string.IsNullOrWhiteSpace(refreshToken))
                {
                    // Crear un nuevo HttpClient para la petición de refresh, sin la autorización
                    // Utilizar la misma base address de la request original
                    var baseAddress = new Uri(request.RequestUri.GetLeftPart(UriPartial.Authority));
                    using var refreshClient = new HttpClient { BaseAddress = baseAddress };
                    
                    var refreshReq = new RefreshTokenRequest { RefreshToken = refreshToken };
                    var refreshResp = await refreshClient.PostAsJsonAsync("/api/auth/refresh", refreshReq, cancellationToken);
                    
                    if (refreshResp.IsSuccessStatusCode)
                    {
                        var result = await refreshResp.Content.ReadFromJsonAsync<LoginResponse>(cancellationToken: cancellationToken);
                        if (result?.Exito == true && !string.IsNullOrWhiteSpace(result.Token))
                        {
                            // Actualizar tokens
                            await _authStateProvider.MarkUserAsAuthenticated(result.Token, result.RefreshToken ?? "");

                            // Clonar e intentar la request original de nuevo
                            var clonedReq = await CloneRequest(request);
                            clonedReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", result.Token);
                            
                            // Disponer de la respuesta anterior fallida
                            response.Dispose();
                            
                            // Enviar request clonada
                            response = await base.SendAsync(clonedReq, cancellationToken);
                        }
                    }
                    else
                    {
                        // Refresh token falló, cerrar sesión
                        await _authStateProvider.MarkUserAsLoggedOut();
                    }
                }
            }
            catch (Exception)
            {
                // Ignorar errores en refresh para no crashear la app, devolverá el 401 original
            }
        }

        return response;
    }

    private async Task<HttpRequestMessage> CloneRequest(HttpRequestMessage req)
    {
        var clone = new HttpRequestMessage(req.Method, req.RequestUri);
        
        if (req.Content != null)
        {
            var contentBytes = await req.Content.ReadAsByteArrayAsync();
            clone.Content = new ByteArrayContent(contentBytes);
            
            if (req.Content.Headers != null)
            {
                foreach (var header in req.Content.Headers)
                {
                    clone.Content.Headers.TryAddWithoutValidation(header.Key, header.Value);
                }
            }
        }
        
        foreach (var header in req.Headers)
        {
            clone.Headers.TryAddWithoutValidation(header.Key, header.Value);
        }
        
        foreach (var prop in req.Options)
        {
            clone.Options.Set(new HttpRequestOptionsKey<object>(prop.Key), prop.Value);
        }
        
        return clone;
    }
}
