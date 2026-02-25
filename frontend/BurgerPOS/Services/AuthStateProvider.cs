using System.Net.Http.Headers;
using System.Security.Claims;
using System.Text.Json;
using Microsoft.AspNetCore.Components.Authorization;
using Blazored.LocalStorage;

namespace BurgerPOS.Services;

/// <summary>
/// AuthenticationStateProvider usando Blazored.LocalStorage
/// Maneja el estado de autenticación basado en JWT tokens
/// </summary>
public class AuthStateProvider : AuthenticationStateProvider
{
    private readonly ILocalStorageService _localStorage;
    private readonly HttpClient _httpClient;
    private const string TOKEN_KEY = "authToken";
    private const string REFRESH_TOKEN_KEY = "refreshToken";
    
    // In-memory cache for token so DelegatingHandler can access it
    // without JS Interop (which is unavailable in HttpClient pipeline)
    private string? _cachedToken;
    private string? _cachedRefreshToken;

    public AuthStateProvider(ILocalStorageService localStorage, HttpClient httpClient)
    {
        _localStorage = localStorage;
        _httpClient = httpClient;
    }

    private async Task LogToBrowser(string message)
    {
        // Logging de depuración deshabilitado para evitar ruido en la consola del navegador.
        await Task.CompletedTask;
    }

    public override async Task<AuthenticationState> GetAuthenticationStateAsync()
    {
        await LogToBrowser("🔐 AuthStateProvider: GetAuthenticationStateAsync iniciado");

        // Retry mechanism for LocalStorage timing issues
        int maxRetries = 3;
        int delayMs = 100;

        for (int attempt = 1; attempt <= maxRetries; attempt++)
        {
            try
            {
                await LogToBrowser($"🔐 AuthStateProvider: Intento {attempt}/{maxRetries} - Leyendo token de LocalStorage...");
                var token = await _localStorage.GetItemAsync<string>(TOKEN_KEY);
                await LogToBrowser($"🔐 AuthStateProvider: Token leído: {(string.IsNullOrEmpty(token) ? "NULL/VACIO" : "ENCONTRADO")}");

                if (string.IsNullOrEmpty(token))
                {
                    return new AuthenticationState(
                        new ClaimsPrincipal(new ClaimsIdentity())
                    );
                }

                try
                {
                    var claims = ParseClaimsFromJwt(token);
                    var identity = new ClaimsIdentity(claims, "jwt");
                    var user = new ClaimsPrincipal(identity);

                    // Cache the token in memory for the DelegatingHandler
                    _cachedToken = token?.Trim('"');

                    // INYECTAR DIRECTAMENTE EN EL HTTP CLIENT AQUI
                    _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", _cachedToken);

                    await LogToBrowser($"🔐 AuthStateProvider: Usuario autenticado: {identity.Name}");
                    return new AuthenticationState(user);
                }
                catch (Exception ex)
                {
                    await LogToBrowser($"🔐 AuthStateProvider: Error parseando token: {ex.Message}");
                    // Token inválido - limpiar
                    await _localStorage.RemoveItemAsync(TOKEN_KEY);
                    await _localStorage.RemoveItemAsync(REFRESH_TOKEN_KEY);
                    _httpClient.DefaultRequestHeaders.Authorization = null;
                    return new AuthenticationState(
                        new ClaimsPrincipal(new ClaimsIdentity())
                    );
                }
            }
            catch (InvalidOperationException ex)
            {
                await LogToBrowser($"🔐 AuthStateProvider: InvalidOperationException en intento {attempt}/{maxRetries}: {ex.Message}");

                // Si es el último intento, devolver no autenticado
                if (attempt >= maxRetries)
                {
                    await LogToBrowser("🔐 AuthStateProvider: Máximo de reintentos alcanzado. Retornando no autenticado.");
                    return new AuthenticationState(
                        new ClaimsPrincipal(new ClaimsIdentity())
                    );
                }

                // Esperar antes del siguiente intento
                await Task.Delay(delayMs);
                delayMs *= 2; // Exponential backoff
            }
            catch (Exception ex)
            {
                await LogToBrowser($"🔐 AuthStateProvider: Error general: {ex.Message}");
                return new AuthenticationState(
                    new ClaimsPrincipal(new ClaimsIdentity())
                );
            }
        }

        // Fallback (no debería llegar aquí, pero por seguridad)
        _httpClient.DefaultRequestHeaders.Authorization = null;
        return new AuthenticationState(
            new ClaimsPrincipal(new ClaimsIdentity())
        );
    }

    /// <summary>
    /// Marcar usuario como autenticado y guardar token
    /// </summary>
    public async Task MarkUserAsAuthenticated(string token, string refreshToken = "")
    {
        try
        {
            await LogToBrowser("🔐 AuthStateProvider: MarkUserAsAuthenticated llamado");
            await _localStorage.SetItemAsync(TOKEN_KEY, token);
            if (!string.IsNullOrEmpty(refreshToken))
            {
                await _localStorage.SetItemAsync(REFRESH_TOKEN_KEY, refreshToken);
            }
            await LogToBrowser("🔐 AuthStateProvider: Token guardado en LocalStorage");
            
            var claims = ParseClaimsFromJwt(token);
            var identity = new ClaimsIdentity(claims, "jwt");
            var user = new ClaimsPrincipal(identity);

            // Cache the token in memory
            _cachedToken = token;
            _cachedRefreshToken = refreshToken;

            _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

            NotifyAuthenticationStateChanged(Task.FromResult(new AuthenticationState(user)));
        }
        catch (InvalidOperationException)
        {
            // Ignorar error de JS Interop durante prerendering
        }
    }

    /// <summary>
    /// Marcar usuario como desconectado y eliminar token
    /// </summary>
    public async Task MarkUserAsLoggedOut()
    {
        await LogToBrowser("🔐 AuthStateProvider: MarkUserAsLoggedOut llamado");
        await _localStorage.RemoveItemAsync(TOKEN_KEY);
        await _localStorage.RemoveItemAsync(REFRESH_TOKEN_KEY);
        _httpClient.DefaultRequestHeaders.Authorization = null;
        _cachedToken = null;
        _cachedRefreshToken = null;
        
        var anonymous = new ClaimsPrincipal(new ClaimsIdentity());
        NotifyAuthenticationStateChanged(Task.FromResult(new AuthenticationState(anonymous)));
    }

    /// <summary>
    /// Obtener el token almacenado
    /// </summary>
    public async Task<string?> GetToken()
    {
        try
        {
            var token = await _localStorage.GetItemAsync<string>(TOKEN_KEY);
            var cleanToken = token?.Trim('"');
            if (!string.IsNullOrWhiteSpace(cleanToken))
            {
                _cachedToken = cleanToken;
            }
            return cleanToken;
        }
        catch (InvalidOperationException)
        {
            return _cachedToken;
        }
    }

    /// <summary>
    /// Obtener el refresh token almacenado
    /// </summary>
    public async Task<string?> GetRefreshToken()
    {
        try
        {
            var token = await _localStorage.GetItemAsync<string>(REFRESH_TOKEN_KEY);
            var cleanToken = token?.Trim('"');
            if (!string.IsNullOrWhiteSpace(cleanToken))
            {
                _cachedRefreshToken = cleanToken; // Update cache
            }
            return cleanToken;
        }
        catch (InvalidOperationException)
        {
            return _cachedRefreshToken;
        }
    }

    /// <summary>
    /// Parsear claims del JWT token
    /// </summary>
    private List<Claim> ParseClaimsFromJwt(string jwt)
    {
        var claims = new List<Claim>();
        var payload = jwt.Split('.')[1];
        
        var jsonBytes = ParseBase64WithoutPadding(payload);
        var keyValuePairs = JsonSerializer.Deserialize<Dictionary<string, object>>(jsonBytes);

        if (keyValuePairs != null)
        {
            // Email
            if (keyValuePairs.TryGetValue("email", out var email))
            {
                claims.Add(new Claim(ClaimTypes.Email, email.ToString() ?? ""));
                claims.Add(new Claim(ClaimTypes.Name, email.ToString() ?? ""));
            }

            // Username
            if (keyValuePairs.TryGetValue("username", out var username))
            {
                claims.Add(new Claim("username", username.ToString() ?? ""));
                // Si no hay email, usar username como Name
                if (!keyValuePairs.ContainsKey("email"))
                {
                    claims.Add(new Claim(ClaimTypes.Name, username.ToString() ?? ""));
                }
            }

            // Rol
            if (keyValuePairs.TryGetValue("rol", out var rol))
            {
                claims.Add(new Claim(ClaimTypes.Role, rol.ToString() ?? ""));
            }

            // Usuario ID
            if (keyValuePairs.TryGetValue("usuario_id", out var usuarioId))
            {
                claims.Add(new Claim("usuario_id", usuarioId.ToString() ?? ""));
            }

            // Agregar todos los otros claims
            foreach (var kvp in keyValuePairs)
            {
                if (kvp.Key != "email" && kvp.Key != "username" && kvp.Key != "rol" && kvp.Key != "usuario_id")
                {
                    claims.Add(new Claim(kvp.Key, kvp.Value.ToString() ?? ""));
                }
            }
        }

        return claims;
    }

    /// <summary>
    /// Parsear Base64 sin padding
    /// </summary>
    private byte[] ParseBase64WithoutPadding(string base64)
    {
        switch (base64.Length % 4)
        {
            case 2: base64 += "=="; break;
            case 3: base64 += "="; break;
        }
        return Convert.FromBase64String(base64);
    }
}
