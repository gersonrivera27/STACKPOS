using System.Net.Http.Json;
using BurgerPOS.Models;

namespace BurgerPOS.Services;

public class PosApiService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<PosApiService> _logger;

    public PosApiService(HttpClient httpClient, ILogger<PosApiService> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }

    // ==================== HEALTH CHECK ====================

    public async Task<bool> TestConnectionAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync("/health");
            if (response.IsSuccessStatusCode)
            {
                var health = await response.Content.ReadFromJsonAsync<HealthResponse>();
                _logger.LogInformation("Backend conectado: {Status}", health?.Status);
                return true;
            }
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error conectando al backend");
            return false;
        }
    }

    // ==================== CONFIGURATION ====================

    public async Task<string?> GetGoogleMapsApiKeyAsync()
    {
        try
        {
            var response = await _httpClient.GetFromJsonAsync<PublicConfigResponse>("/api/config/public");
            return response?.GoogleMapsApiKey;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo Google Maps API key");
            return null;
        }
    }

    // ==================== GEOCODING ====================

    public async Task<GeocodeResponse?> GeocodeEircodeAsync(string eircode)
    {
        try
        {
            _logger.LogInformation("Geocoding Eircode: {Eircode}", eircode);

            var response = await _httpClient.GetFromJsonAsync<GeocodeResponse>(
                $"/api/geocoding/eircode?code={Uri.EscapeDataString(eircode)}");

            if (response?.Found == true)
            {
                _logger.LogInformation("✅ Eircode geocoded: {Address}", response.FormattedAddress);
            }
            else
            {
                _logger.LogWarning("❌ Eircode not found: {Eircode}", eircode);
            }

            return response;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error geocoding Eircode");
            return null;
        }
    }

    // ==================== CUSTOMERS ====================

    public async Task<List<Customer>> GetCustomersAsync(string? search = null, int limit = 100)
    {
        try
        {
            var url = $"/api/customers?limit={limit}";
            if (!string.IsNullOrEmpty(search))
            {
                url += $"&search={Uri.EscapeDataString(search)}";
            }

            var customers = await _httpClient.GetFromJsonAsync<List<Customer>>(url);
            return customers ?? new List<Customer>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo clientes");
            return new List<Customer>();
        }
    }

    public async Task<CustomerSearchResponse?> SearchCustomerByPhoneAsync(string phone)
    {
        try
        {
            _logger.LogInformation("Buscando cliente por teléfono: {Phone}", phone);

            var response = await _httpClient.GetAsync($"/api/customers/search-by-phone/{Uri.EscapeDataString(phone)}");

            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<CustomerSearchResponse>();
            }

            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error buscando cliente por teléfono");
            return null;
        }
    }

    public async Task<List<Customer>?> SearchCustomersAsync(string query)
    {
        try
        {
            _logger.LogInformation("Buscando clientes con query: {Query}", query);

            var response = await _httpClient.GetAsync($"/api/customers?search={Uri.EscapeDataString(query)}&limit=10");

            if (response.IsSuccessStatusCode)
            {
                var customers = await response.Content.ReadFromJsonAsync<List<Customer>>();
                _logger.LogInformation("Encontrados {Count} clientes", customers?.Count ?? 0);
                return customers;
            }
            else
            {
                _logger.LogWarning("Error buscando clientes: {StatusCode}", response.StatusCode);
                return new List<Customer>();
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Excepción buscando clientes");
            return new List<Customer>();
        }
    }

    // ==================== MODIFIERS ====================
    public async Task<List<Modifier>> GetModifiersAsync()
    {
        try
        {
            var modifiers = await _httpClient.GetFromJsonAsync<List<Modifier>>("/api/modifiers");
            return modifiers ?? new List<Modifier>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo modificadores");
            return new List<Modifier>();
        }
    }

    public async Task<Customer?> CreateCustomerAsync(CustomerCreate customer)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/api/customers", customer);
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<Customer>();
            }
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creando cliente");
            return null;
        }
    }



    public async Task<Customer?> UpdateCustomerAsync(int customerId, CustomerCreate customer)
    {
        try
        {
            var response = await _httpClient.PutAsJsonAsync($"/api/customers/{customerId}", customer);
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<Customer>();
            }
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error actualizando cliente");
            return null;
        }
    }



    // ==================== PRODUCTS ====================

    public async Task<List<Product>> GetProductsAsync(int? categoryId = null, bool includeInactive = false)
    {
        try
        {
            // available_only = !includeInactive
            var availableOnly = !includeInactive;
            var url = $"/api/products?available_only={availableOnly.ToString().ToLower()}";
            if (categoryId.HasValue)
            {
                url += $"&category_id={categoryId.Value}";
            }

            var products = await _httpClient.GetFromJsonAsync<List<Product>>(url);
            return products ?? new List<Product>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo productos");
            return new List<Product>();
        }
    }

    public async Task<Product?> CreateProductAsync(ProductCreate product)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/api/products", product);
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<Product>();
            }
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creando producto");
            return null;
        }
    }

    public async Task<Product?> UpdateProductAsync(int productId, ProductUpdate product)
    {
        try
        {
            var response = await _httpClient.PutAsJsonAsync($"/api/products/{productId}", product);
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<Product>();
            }
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error actualizando producto");
            return null;
        }
    }

    public async Task<bool> DeleteProductAsync(int productId)
    {
        try
        {
            var response = await _httpClient.DeleteAsync($"/api/products/{productId}");
            return response.IsSuccessStatusCode;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error eliminando producto");
            return false;
        }
    }

    public async Task<string?> UploadImageAsync(Microsoft.AspNetCore.Components.Forms.IBrowserFile file)
    {
        try
        {
            using var content = new MultipartFormDataContent();
            using var stream = file.OpenReadStream(maxAllowedSize: 10 * 1024 * 1024); // 10MB max
            using var fileContent = new StreamContent(stream);
            fileContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue(file.ContentType);
            
            content.Add(fileContent, "file", file.Name);

            var response = await _httpClient.PostAsync("/api/uploads/images", content);
            
            if (response.IsSuccessStatusCode)
            {
                var result = await response.Content.ReadFromJsonAsync<Dictionary<string, string>>();
                return result?["url"];
            }
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error subiendo imagen");
            return null;
        }
    }

    // ==================== ORDERS ====================

    public async Task<List<Order>> GetOrdersAsync(string? status = null, int limit = 100, bool activeSessionOnly = false)
    {
        try
        {
            var url = $"/api/orders?limit={limit}";
            if (!string.IsNullOrEmpty(status))
            {
                url += $"&status={status}";
            }
            
            if (activeSessionOnly)
            {
                url += "&only_active_session=true";
            }

            var orders = await _httpClient.GetFromJsonAsync<List<Order>>(url);
            return orders ?? new List<Order>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo órdenes");
            return new List<Order>();
        }
    }

    // ==================== CATEGORIES ====================

    public async Task<List<Category>> GetCategoriesAsync()
    {
        try
        {
            var categories = await _httpClient.GetFromJsonAsync<List<Category>>("/api/categories");
            return categories ?? new List<Category>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo categorías");
            return new List<Category>();
        }
    }

    public async Task<Category?> CreateCategoryAsync(CategoryCreate category)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/api/categories", category);
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<Category>();
            }
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creando categoría");
            return null;
        }
    }

    public async Task<Category?> UpdateCategoryAsync(int id, CategoryUpdate category)
    {
        try
        {
            var response = await _httpClient.PutAsJsonAsync($"/api/categories/{id}", category);
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<Category>();
            }
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error actualizando categoría");
            return null;
        }
    }

    public async Task<bool> DeleteCategoryAsync(int id)
    {
        try
        {
            var response = await _httpClient.DeleteAsync($"/api/categories/{id}");
            return response.IsSuccessStatusCode;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error eliminando categoría");
            return false;
        }
    }
    
     public async Task<Order?> CreateOrderAsync(OrderCreate orderData)
    {
        try
        {
            _logger.LogInformation("Creando orden para: {CustomerName}", orderData.CustomerName);
            
            var response = await _httpClient.PostAsJsonAsync("/api/orders", orderData);
            
            if (response.IsSuccessStatusCode)
            {
                var order = await response.Content.ReadFromJsonAsync<Order>();
                _logger.LogInformation("Orden creada exitosamente: {OrderNumber}", order?.OrderNumber);
                return order;
            }
            else
            {
                var errorContent = await response.Content.ReadAsStringAsync();
                _logger.LogError("Error creando orden: {StatusCode} - {Error}", response.StatusCode, errorContent);
                return null;
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Excepción creando orden");
            return null;
        }
    }
    
    public async Task<OrderWithDetails?> GetOrderDetailsAsync(int orderId)
    {
        try
        {
            var order = await _httpClient.GetFromJsonAsync<OrderWithDetails>($"/api/orders/{orderId}");
            return order;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo detalles de orden");
            return null;
        }
    }

    public async Task<OrderWithDetails?> GetOrderAsync(int orderId)
    {
        return await GetOrderDetailsAsync(orderId);
    }

    public async Task<Order?> UpdateOrderStatusAsync(int orderId, string status)
    {
        try
        {
            // Assuming the backend endpoint is PATCH /api/orders/{id}/status?new_status={status}
            // or expecting a JSON body. Let's check the backend router again if needed, 
            // but based on previous read it was PATCH /{order_id}/status with query param or body?
            // The backend router signature was:
            // update_order_status(order_id: int, new_status: OrderStatus, ...)
            // It usually expects query param if not specified as Body.
            
            var response = await _httpClient.PatchAsync($"/api/orders/{orderId}/status?new_status={status}", null);
            
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<Order>();
            }
            
            _logger.LogError("Error actualizando estado de orden: {StatusCode}", response.StatusCode);
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Excepción actualizando estado de orden");
            return null;
        }
    }

    // ==================== PAYMENTS ====================

    public async Task<PaymentResponse?> CreatePaymentAsync(PaymentCreate payment)
    {
        try
        {
            _logger.LogInformation("Procesando pago para orden: {OrderId}", payment.OrderId);
            
            var response = await _httpClient.PostAsJsonAsync("/api/cash/payments", payment);
            
            if (response.IsSuccessStatusCode)
            {
                var result = await response.Content.ReadFromJsonAsync<PaymentResponse>();
                _logger.LogInformation("Pago procesado exitosamente: {PaymentId}", result?.Id);
                return result;
            }
            else
            {
                var errorContent = await response.Content.ReadAsStringAsync();
                _logger.LogError("Error procesando pago: {StatusCode} - {Error}", response.StatusCode, errorContent);
                return null;
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Excepción procesando pago");
            return null;
        }
    }

    // ==================== CASH SESSIONS ====================

    public async Task<CashSession?> GetActiveCashSessionAsync(int? userId = null)
    {
        try
        {
            var url = "/api/cash/sessions/active";
            if (userId.HasValue)
            {
                url += $"?user_id={userId.Value}";
            }
            
            var response = await _httpClient.GetAsync(url);
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<CashSession>();
            }
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo sesión de caja activa");
            return null;
        }
    }

    public async Task<CashSession?> OpenCashSessionAsync(CashSessionCreate session)
    {
        try
        {
            _logger.LogInformation("Abriendo sesión de caja con monto: {Amount}", session.OpeningAmount);
            
            var response = await _httpClient.PostAsJsonAsync("/api/cash/sessions", session);
            
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<CashSession>();
            }
            else
            {
                var errorContent = await response.Content.ReadAsStringAsync();
                _logger.LogError("Error abriendo sesión de caja: {Error}", errorContent);
                return null;
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Excepción abriendo sesión de caja");
            return null;
        }
    }

    public async Task<CashSession?> CloseCashSessionAsync(int sessionId, CashSessionClose closeData)
    {
        try
        {
            _logger.LogInformation("Cerrando sesión de caja {SessionId}", sessionId);
            
            var response = await _httpClient.PostAsJsonAsync($"/api/cash/sessions/{sessionId}/close", closeData);
            
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<CashSession>();
            }
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Excepción cerrando sesión de caja");
            return null;
        }
    }

    public async Task<CashSession?> GetCashSessionAsync(int sessionId)
    {
        try
        {
            return await _httpClient.GetFromJsonAsync<CashSession>($"/api/cash/sessions/{sessionId}");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo sesión de caja");
            return null;
        }
    }

    public async Task<List<CashSession>> GetCashSessionsAsync(string? status = null)
    {
        try
        {
            var url = "/api/cash/sessions";
            if (!string.IsNullOrEmpty(status))
            {
                url += $"?status={status}";
            }
            
            var response = await _httpClient.GetAsync(url);
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<List<CashSession>>() ?? new List<CashSession>();
            }
            return new List<CashSession>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo historial de sesiones");
            return new List<CashSession>();
        }
    }
    public async Task<PaymentResponse?> GetPaymentByOrderAsync(int orderId)
    {
        try
        {
            var response = await _httpClient.GetAsync($"/api/cash/payments/order/{orderId}");
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<PaymentResponse>();
            }
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo pago de orden {OrderId}", orderId);
            return null;
        }
    }

    // ==================== REPORTS ====================

    public async Task<DailySalesResponse?> GetDailySalesReportAsync(DateTime? date = null)
    {
        try
        {
            var url = "/api/reports/daily-sales";
            if (date.HasValue)
            {
                url += $"?report_date={date.Value:yyyy-MM-dd}";
            }

            var response = await _httpClient.GetAsync(url);
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<DailySalesResponse>();
            }
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo reporte de ventas diarias");
            return null;
        }
    }

    public async Task<TopProductsResponse?> GetTopProductsReportAsync(DateTime? from = null, DateTime? to = null, int limit = 10)
    {
        try
        {
            var url = $"/api/reports/top-products?limit={limit}";
            if (from.HasValue) url += $"&date_from={from.Value:yyyy-MM-dd}";
            if (to.HasValue) url += $"&date_to={to.Value:yyyy-MM-dd}";

            var response = await _httpClient.GetAsync(url);
            if (response.IsSuccessStatusCode)
            {
                var result = await response.Content.ReadFromJsonAsync<TopProductsResponse>();
                return result;
            }
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo reporte de productos top");
            return null;
        }
    }
    // ==================== TABLES ====================

    public async Task<List<Table>> GetTablesAsync()
    {
        try
        {
            var tables = await _httpClient.GetFromJsonAsync<List<Table>>("/api/tables");
            return tables ?? new List<Table>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error obteniendo mesas");
            return new List<Table>();
        }
    }

    public async Task<bool> UpdateTablePositionAsync(int tableId, int x, int y)
    {
        try
        {
            var response = await _httpClient.PatchAsync($"/api/tables/{tableId}/position?x={x}&y={y}", null);
            return response.IsSuccessStatusCode;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error actualizando posición de mesa");
            return false;
        }
    }

    public async Task<bool> UpdateTableStatusAsync(int tableId, bool isOccupied)
    {
        try
        {
            var response = await _httpClient.PatchAsync($"/api/tables/{tableId}/status?is_occupied={isOccupied.ToString().ToLower()}", null);
            return response.IsSuccessStatusCode;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error actualizando estado de mesa");
            return false;
        }
    }

    public async Task<OrderWithDetails?> UpdateOrderItemsAsync(int orderId, OrderItemsUpdate update)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync($"/api/orders/{orderId}/items", update);
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<OrderWithDetails>();
            }
            _logger.LogWarning("Fallo al actualizar items de orden {OrderId}: {Status}", orderId, response.StatusCode);
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error actualizando items de orden {OrderId}", orderId);
            return null;
        }
    }
}
