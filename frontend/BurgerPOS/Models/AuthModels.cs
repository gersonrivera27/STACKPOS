namespace BurgerPOS.Models;

using System.Text.Json.Serialization;

/// <summary>
/// Request body para login
/// </summary>
public class LoginRequest
{
    [JsonPropertyName("username_or_email")]
    public string Username { get; set; } = string.Empty;
    
    [JsonPropertyName("password")]
    public string Password { get; set; } = string.Empty;
}

/// <summary>
/// Información del usuario
/// </summary>
public class UsuarioDto
{
    [JsonPropertyName("id")]
    public int Id { get; set; }
    
    [JsonPropertyName("username")]
    public string Username { get; set; } = string.Empty;
    
    [JsonPropertyName("email")]
    public string Email { get; set; } = string.Empty;
    
    [JsonPropertyName("full_name")]
    public string? FullName { get; set; }
    
    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty;
    
    [JsonPropertyName("is_active")]
    public bool IsActive { get; set; }
}

/// <summary>
/// Response completo del login
/// </summary>
public class LoginResponse
{
    [JsonPropertyName("exito")]
    public bool Exito { get; set; }
    
    [JsonPropertyName("mensaje")]
    public string Mensaje { get; set; } = string.Empty;
    
    [JsonPropertyName("token")]
    public string? Token { get; set; }
    
    [JsonPropertyName("refresh_token")]
    public string? RefreshToken { get; set; }
    
    [JsonPropertyName("usuario")]
    public UsuarioDto? Usuario { get; set; }
}

/// <summary>
/// Request body for refreshing the token
/// </summary>
public class RefreshTokenRequest
{
    [JsonPropertyName("refresh_token")]
    public string RefreshToken { get; set; } = string.Empty;
}

/// <summary>
/// Request body for logout — revokes the refresh token server-side
/// </summary>
public class LogoutRequest
{
    [JsonPropertyName("refresh_token")]
    public string RefreshToken { get; set; } = string.Empty;
}
