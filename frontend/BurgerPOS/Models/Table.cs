using System.Text.Json.Serialization;

namespace BurgerPOS.Models;

public class Table
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("table_number")]
    public int TableNumber { get; set; }

    [JsonPropertyName("is_occupied")]
    public bool IsOccupied { get; set; }

    [JsonPropertyName("x")]
    public int X { get; set; }

    [JsonPropertyName("y")]
    public int Y { get; set; }

    [JsonPropertyName("active_order")]
    public ActiveOrderInfo? ActiveOrder { get; set; }
}

public class ActiveOrderInfo
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("customer_name")]
    public string? CustomerName { get; set; }

    [JsonPropertyName("total")]
    public decimal Total { get; set; }

    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }
    
    [JsonPropertyName("time_elapsed")]
    public string? TimeElapsed { get; set; }
}
