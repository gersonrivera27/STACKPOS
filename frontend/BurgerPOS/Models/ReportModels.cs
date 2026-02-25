using System.Text.Json.Serialization;

namespace BurgerPOS.Models;

public class DailySalesResponse
{
    [JsonPropertyName("date")]
    public DateTime Date { get; set; }

    [JsonPropertyName("summary")]
    public SalesSummary Summary { get; set; } = new();

    [JsonPropertyName("by_order_type")]
    public List<SalesByType> ByOrderType { get; set; } = new();
}

public class SalesSummary
{
    [JsonPropertyName("total_orders")]
    public int TotalOrders { get; set; }

    [JsonPropertyName("total_sales")]
    public decimal TotalSales { get; set; }

    [JsonPropertyName("average_ticket")]
    public decimal AverageTicket { get; set; }

    [JsonPropertyName("total_tax")]
    public decimal TotalTax { get; set; }

    [JsonPropertyName("completed_orders")]
    public int CompletedOrders { get; set; }

    [JsonPropertyName("cancelled_orders")]
    public int CancelledOrders { get; set; }
}

public class SalesByType
{
    [JsonPropertyName("order_type")]
    public string OrderType { get; set; } = "";

    [JsonPropertyName("count")]
    public int Count { get; set; }

    [JsonPropertyName("total")]
    public decimal Total { get; set; }
}

public class TopProductsResponse
{
    [JsonPropertyName("date_from")]
    public DateTime? DateFrom { get; set; }

    [JsonPropertyName("date_to")]
    public DateTime? DateTo { get; set; }

    [JsonPropertyName("top_products")]
    public List<TopProductItem> TopProducts { get; set; } = new();
}

public class TopProductItem
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("category")]
    public string Category { get; set; } = "";

    [JsonPropertyName("times_ordered")]
    public int TimesOrdered { get; set; }

    [JsonPropertyName("total_quantity")]
    public int TotalQuantity { get; set; }

    [JsonPropertyName("total_revenue")]
    public decimal TotalRevenue { get; set; }
}
