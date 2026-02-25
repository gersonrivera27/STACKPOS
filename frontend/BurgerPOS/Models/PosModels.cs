using System.Text.Json.Serialization;

namespace BurgerPOS.Models;

public class Modifier
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("price")]
    public decimal Price { get; set; }

    [JsonPropertyName("modifier_type")]
    public string? ModifierType { get; set; }

    [JsonPropertyName("is_active")]
    public bool IsActive { get; set; } = true;
}

// ==================== CATEGORY ====================
public class Category
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }
}

public class CategoryCreate
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("description")]
    public string? Description { get; set; }
}

public class CategoryUpdate
{
    [JsonPropertyName("name")]
    public string? Name { get; set; }

    [JsonPropertyName("description")]
    public string? Description { get; set; }
}

// ==================== CUSTOMER ====================
public class Customer
{
    [JsonPropertyName("id")]
    public int Id { get; set; }
    
    [JsonPropertyName("phone")]
    public string Phone { get; set; } = "";
    
    [JsonPropertyName("name")]
    public string Name { get; set; } = "";
    
    [JsonPropertyName("email")]
    public string? Email { get; set; }
    
    [JsonPropertyName("address_line1")]
    public string? AddressLine1 { get; set; }
    
    [JsonPropertyName("address_line2")]
    public string? AddressLine2 { get; set; }
    
    [JsonPropertyName("city")]
    public string City { get; set; } = "Drogheda";
    
    [JsonPropertyName("county")]
    public string County { get; set; } = "Louth";
    
    [JsonPropertyName("eircode")]
    public string? Eircode { get; set; }
    
    [JsonPropertyName("country")]
    public string Country { get; set; } = "Ireland";
    
    [JsonPropertyName("latitude")]
    public double? Latitude { get; set; }
    
    [JsonPropertyName("longitude")]
    public double? Longitude { get; set; }
    
    [JsonPropertyName("notes")]
    public string? Notes { get; set; }
    
    [JsonPropertyName("is_active")]
    public bool IsActive { get; set; } = true;
    
    [JsonPropertyName("total_orders")]
    public int TotalOrders { get; set; }
    
    [JsonPropertyName("total_spent")]
    public decimal TotalSpent { get; set; }
    
    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }
}

public class CustomerCreate
{
    [JsonPropertyName("phone")]
    public string Phone { get; set; } = "";
    
    [JsonPropertyName("name")]
    public string Name { get; set; } = "";
    
    [JsonPropertyName("email")]
    public string? Email { get; set; }
    
    [JsonPropertyName("address_line1")]
    public string? AddressLine1 { get; set; }
    
    [JsonPropertyName("address_line2")]
    public string? AddressLine2 { get; set; }
    
    [JsonPropertyName("city")]
    public string City { get; set; } = "Drogheda";
    
    [JsonPropertyName("county")]
    public string County { get; set; } = "Louth";
    
    [JsonPropertyName("eircode")]
    public string? Eircode { get; set; }
    
    [JsonPropertyName("country")]
    public string Country { get; set; } = "Ireland";
    
    [JsonPropertyName("latitude")]
    public double? Latitude { get; set; }
    
    [JsonPropertyName("longitude")]
    public double? Longitude { get; set; }
    
    [JsonPropertyName("notes")]
    public string? Notes { get; set; }
}

public class CustomerSearchResponse
{
    [JsonPropertyName("found")]
    public bool Found { get; set; }
    
    [JsonPropertyName("customer")]
    public Customer? Customer { get; set; }
}

// ==================== PRODUCT ====================
public class Product
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("category_id")]
    public int CategoryId { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [JsonPropertyName("price")]
    public decimal Price { get; set; }

    [JsonPropertyName("image_url")]
    public string? ImageUrl { get; set; }

    [JsonPropertyName("is_available")]
    public bool IsAvailable { get; set; } = true;

    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }
}

public class ProductCreate
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("category_id")]
    public int CategoryId { get; set; }

    [JsonPropertyName("price")]
    public decimal Price { get; set; }

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [JsonPropertyName("image_url")]
    public string? ImageUrl { get; set; }

    [JsonPropertyName("is_available")]
    public bool IsAvailable { get; set; } = true;

    [JsonPropertyName("sort_order")]
    public int SortOrder { get; set; } = 0;
}

public class ProductUpdate
{
    [JsonPropertyName("name")]
    public string? Name { get; set; }

    [JsonPropertyName("category_id")]
    public int? CategoryId { get; set; }

    [JsonPropertyName("price")]
    public decimal? Price { get; set; }

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [JsonPropertyName("image_url")]
    public string? ImageUrl { get; set; }

    [JsonPropertyName("is_available")]
    public bool? IsAvailable { get; set; }

    [JsonPropertyName("sort_order")]
    public int? SortOrder { get; set; }
}

// ==================== ORDER ====================
public class Order
{
    [JsonPropertyName("id")]
    public int Id { get; set; }
    
    [JsonPropertyName("order_number")]
    public string OrderNumber { get; set; } = "";
    
    [JsonPropertyName("customer_name")]
    public string? CustomerName { get; set; }

    [JsonPropertyName("customer_phone")]
    public string? CustomerPhone { get; set; }

    [JsonPropertyName("customer_address")]
    public string? CustomerAddress { get; set; }
    
    [JsonPropertyName("order_type")]
    public string OrderType { get; set; } = "dine-in";
    
    [JsonPropertyName("status")]
    public string Status { get; set; } = "pending";
    
    [JsonPropertyName("subtotal")]
    public decimal Subtotal { get; set; }
    
    [JsonPropertyName("tax")]
    public decimal Tax { get; set; }
    
    [JsonPropertyName("total")]
    public decimal Total { get; set; }
    
    [JsonPropertyName("payment_method")]
    public string? PaymentMethod { get; set; }

    [JsonPropertyName("has_payment")]
    public bool HasPayment { get; set; }
    
    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }

    [JsonPropertyName("completed_at")]
    public DateTime? CompletedAt { get; set; }

    [JsonPropertyName("user_id")]
    public int? UserId { get; set; }

    [JsonPropertyName("waiter_name")]
    public string? WaiterName { get; set; }

    [JsonPropertyName("table_id")]
    public int? TableId { get; set; }
}

// ==================== HEALTH CHECK ====================
public class HealthResponse
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "";
    
    [JsonPropertyName("timestamp")]
    public DateTime Timestamp { get; set; }
}

// ==================== ORDER CREATION ====================

public class CartItem
{
    // When editing an existing order, keep reference to order_items.id
    public int? OrderItemId { get; set; }
    public int ProductId { get; set; }
    public string ProductName { get; set; } = string.Empty;
    public decimal UnitPrice { get; set; }
    public int Quantity { get; set; }
    public string? SpecialInstructions { get; set; }
    public List<Modifier> SelectedModifiers { get; set; } = new();
    
    public decimal Subtotal => (UnitPrice + SelectedModifiers.Sum(m => m.Price)) * Quantity;
}

public class OrderItemCreate
{
    [JsonPropertyName("product_id")]
    public int ProductId { get; set; }
    
    [JsonPropertyName("quantity")]
    public int Quantity { get; set; }
    
    [JsonPropertyName("special_instructions")]
    public string? SpecialInstructions { get; set; }

    [JsonPropertyName("modifier_ids")]
    public List<int> ModifierIds { get; set; } = new();
}

public class OrderCreate
{
    [JsonPropertyName("customer_name")]
    public string CustomerName { get; set; } = string.Empty;
    
    [JsonPropertyName("order_type")]
    public string OrderType { get; set; } = string.Empty;
    
    [JsonPropertyName("items")]
    public List<OrderItemCreate> Items { get; set; } = new();
    
    [JsonPropertyName("notes")]
    public string? Notes { get; set; }
    
    [JsonPropertyName("table_id")]
    public int? TableId { get; set; }

    [JsonPropertyName("user_id")]
    public int? UserId { get; set; }
    
    [JsonPropertyName("payment_method")]
    public string? PaymentMethod { get; set; }

    [JsonPropertyName("status")]
    public string? Status { get; set; }
}

public class OrderItemsUpdate
{
    [JsonPropertyName("add_items")]
    public List<OrderItemCreate> AddItems { get; set; } = new();

    [JsonPropertyName("remove_item_ids")]
    public List<int> RemoveItemIds { get; set; } = new();
}

public class OrderItem
{
    [JsonPropertyName("id")]
    public int Id { get; set; }
    
    [JsonPropertyName("order_id")]
    public int OrderId { get; set; }
    
    [JsonPropertyName("product_id")]
    public int ProductId { get; set; }
    
    [JsonPropertyName("quantity")]
    public int Quantity { get; set; }
    
    [JsonPropertyName("unit_price")]
    public decimal UnitPrice { get; set; }
    
    [JsonPropertyName("subtotal")]
    public decimal Subtotal { get; set; }
    
    [JsonPropertyName("special_instructions")]
    public string? SpecialInstructions { get; set; }
    
    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }
    
    [JsonPropertyName("product_name")]
    public string? ProductName { get; set; }

    [JsonPropertyName("modifiers")]
    public List<OrderItemModifier> Modifiers { get; set; } = new();
}

public class OrderItemModifier
{
    [JsonPropertyName("id")]
    public int Id { get; set; }
    
    [JsonPropertyName("modifier_id")]
    public int ModifierId { get; set; }
    
    [JsonPropertyName("modifier_name")]
    public string ModifierName { get; set; } = "";
    
    [JsonPropertyName("additional_price")]
    public decimal AdditionalPrice { get; set; }
}

public class OrderWithDetails : Order
{
    [JsonPropertyName("items")]
    public List<OrderItem> Items { get; set; } = new();
}

// ==================== PAYMENT ====================
public class PaymentCreate
{
    [JsonPropertyName("order_id")]
    public int OrderId { get; set; }
    
    [JsonPropertyName("payment_type")]
    public string PaymentType { get; set; } = "cash";
    
    [JsonPropertyName("cash_amount")]
    public decimal CashAmount { get; set; }
    
    [JsonPropertyName("card_amount")]
    public decimal CardAmount { get; set; }
    
    [JsonPropertyName("tip_amount")]
    public decimal TipAmount { get; set; }
}

public class PaymentResponse
{
    [JsonPropertyName("id")]
    public int Id { get; set; }
    
    [JsonPropertyName("order_id")]
    public int OrderId { get; set; }
    
    [JsonPropertyName("payment_type")]
    public string PaymentType { get; set; } = "cash";
    
    [JsonPropertyName("total_amount")]
    public decimal TotalAmount { get; set; }
    
    [JsonPropertyName("cash_amount")]
    public decimal CashAmount { get; set; }
    
    [JsonPropertyName("card_amount")]
    public decimal CardAmount { get; set; }
    
    [JsonPropertyName("tip_amount")]
    public decimal TipAmount { get; set; }
    
    [JsonPropertyName("change_amount")]
    public decimal ChangeAmount { get; set; }
    
    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }
}

// ==================== CASH SESSION ====================
public class CashSessionCreate
{
    [JsonPropertyName("opening_amount")]
    public decimal OpeningAmount { get; set; }
    
    [JsonPropertyName("user_id")]
    public int UserId { get; set; }
    
    [JsonPropertyName("notes")]
    public string? Notes { get; set; }
}

public class CashSessionClose
{
    [JsonPropertyName("closing_amount")]
    public decimal ClosingAmount { get; set; }
    
    [JsonPropertyName("notes")]
    public string? Notes { get; set; }
}

public class CashSession
{
    [JsonPropertyName("id")]
    public int Id { get; set; }
    
    [JsonPropertyName("user_id")]
    public int UserId { get; set; }
    
    [JsonPropertyName("status")]
    public string Status { get; set; } = "open";
    
    [JsonPropertyName("opening_amount")]
    public decimal OpeningAmount { get; set; }
    
    [JsonPropertyName("closing_amount")]
    public decimal? ClosingAmount { get; set; }
    
    [JsonPropertyName("expected_amount")]
    public decimal? ExpectedAmount { get; set; }
    
    [JsonPropertyName("difference")]
    public decimal? Difference { get; set; }
    
    [JsonPropertyName("total_cash_sales")]
    public decimal TotalCashSales { get; set; }
    
    [JsonPropertyName("total_card_sales")]
    public decimal TotalCardSales { get; set; }
    
    [JsonPropertyName("total_sales")]
    public decimal TotalSales { get; set; }
    
    [JsonPropertyName("total_tips")]
    public decimal TotalTips { get; set; }
    
    [JsonPropertyName("orders_count")]
    public int OrdersCount { get; set; }
    
    [JsonPropertyName("opened_at")]
    public DateTime OpenedAt { get; set; }
    
    [JsonPropertyName("closed_at")]
    public DateTime? ClosedAt { get; set; }

    [JsonPropertyName("notes")]
    public string? Notes { get; set; }
}

// ==================== GEOCODING ====================
public class GeocodeResponse
{
    [JsonPropertyName("found")]
    public bool Found { get; set; }

    [JsonPropertyName("address_line1")]
    public string? AddressLine1 { get; set; }

    [JsonPropertyName("address_line2")]
    public string? AddressLine2 { get; set; }

    [JsonPropertyName("city")]
    public string? City { get; set; }

    [JsonPropertyName("county")]
    public string? County { get; set; }

    [JsonPropertyName("eircode")]
    public string? Eircode { get; set; }

    [JsonPropertyName("latitude")]
    public double? Latitude { get; set; }

    [JsonPropertyName("longitude")]
    public double? Longitude { get; set; }

    [JsonPropertyName("formatted_address")]
    public string? FormattedAddress { get; set; }

    [JsonPropertyName("location_type")]
    public string? LocationType { get; set; }
}
