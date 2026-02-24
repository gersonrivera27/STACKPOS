using System.Net.Http.Json;
using BurgerPOS.Models;
using Microsoft.AspNetCore.Components.Authorization;

namespace BurgerPOS.Services;

/// <summary>
/// Servicio de autenticación - maneja login y logout
/// </summary>
public class AuthenticationService
{
    private readonly HttpClient _httpClient;
    private readonly AuthStateProvider _authStateProvider;
    private readonly ILogger<AuthenticationService> _logger;

    public AuthenticationService(
        HttpClient httpClient, 
        AuthenticationStateProvider authStateProvider, 
        ILogger<AuthenticationService> logger)
    {
        _httpClient = httpClient;
        _authStateProvider = (AuthStateProvider)authStateProvider;
        _logger = logger;
    }

    /// <summary>
    /// Iniciar sesión con username o email
    /// </summary>
    public async Task<bool> Login(string username, string password)
    {
        try
        {
            var request = new LoginRequest
            {
                Username = username,
                Password = password
            };

            _logger.LogInformation("Intentando login para usuario: {Username}", username);

            var response = await _httpClient.PostAsJsonAsync("/api/auth/login", request);

            if (response.IsSuccessStatusCode)
            {
                var result = await response.Content.ReadFromJsonAsync<LoginResponse>();
                
                if (result?.Exito == true && !string.IsNullOrEmpty(result.Token))
                {
                    _logger.LogInformation("Login exitoso para usuario: {Username}", username);
                    
                    // Guardar token y actualizar estado de autenticación
                    await _authStateProvider.MarkUserAsAuthenticated(result.Token, result.RefreshToken ?? "");
                    
                    return true;
                }
                else
                {
                    _logger.LogWarning("Login fallido: {Mensaje}", result?.Mensaje ?? "Sin mensaje");
                    return false;
                }
            }
            
            var error = await response.Content.ReadAsStringAsync();
            _logger.LogWarning("Login fallido: {StatusCode} - {Error}", response.StatusCode, error);
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error en login");
            return false;
        }
    }

    /// <summary>
    /// Cerrar sesión
    /// </summary>
    public async Task Logout()
    {
        _logger.LogInformation("Cerrando sesión");
        await _authStateProvider.MarkUserAsLoggedOut();
    }

    /// <summary>
    /// Obtener token actual
    /// </summary>
    public async Task<string?> GetToken()
    {
        return await _authStateProvider.GetToken();
    }

    public async Task<List<User>> GetUsersForLoginAsync()
    {
        try
        {
            return await _httpClient.GetFromJsonAsync<List<User>>("/api/auth/users-list") ?? new List<User>();
        }
        catch
        {
            return new List<User>();
        }
    }

    public async Task<bool> LoginWithPin(int userId, string pin)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/api/auth/pin-login", new { user_id = userId, pin = pin });
            if (response.IsSuccessStatusCode)
            {
                var result = await response.Content.ReadFromJsonAsync<LoginResponse>();
                if (result?.Exito == true && !string.IsNullOrEmpty(result.Token))
                {
                    await _authStateProvider.MarkUserAsAuthenticated(result.Token, result.RefreshToken ?? "");
                    return true;
                }
            }
            return false;
        }
        catch
        {
            return false;
        }
    }
}
