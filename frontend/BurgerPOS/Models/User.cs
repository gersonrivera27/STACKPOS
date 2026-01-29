using System.Text.Json.Serialization;

namespace BurgerPOS.Models;

public class User
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("username")]
    public string Username { get; set; } = "";

    [JsonPropertyName("email")]
    public string Email { get; set; } = "";

    [JsonPropertyName("full_name")]
    public string? FullName { get; set; }

    [JsonPropertyName("role")]
    public string Role { get; set; } = "staff";

    [JsonPropertyName("is_active")]
    public bool IsActive { get; set; }
}
