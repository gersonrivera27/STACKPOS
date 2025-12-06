using Blazored.LocalStorage;
using System.Net.Http.Headers;

namespace BurgerPOS.Services;

/// <summary>
/// DelegatingHandler que inyecta automáticamente el JWT token en las requests
/// </summary>
public class JwtAuthorizationMessageHandler : DelegatingHandler
{
    private readonly ILocalStorageService _localStorage;
    private const string TOKEN_KEY = "authToken";

    public JwtAuthorizationMessageHandler(ILocalStorageService localStorage)
    {
        _localStorage = localStorage;
    }

    protected override async Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request, 
        CancellationToken cancellationToken)
    {
        try
        {
            // Obtener token del LocalStorage
            var token = await _localStorage.GetItemAsync<string>(TOKEN_KEY);
            
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

        return await base.SendAsync(request, cancellationToken);
    }
}
