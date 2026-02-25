using BurgerPOS.Components;
using BurgerPOS.Services;
using Microsoft.AspNetCore.Components.Authorization;
using Blazored.LocalStorage;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

// ============================================
// BLAZORED LOCALSTORAGE
// ============================================
builder.Services.AddBlazoredLocalStorage();

// ============================================
// CONFIGURAR API URL
// ============================================
var apiUrl = builder.Configuration["ApiUrl"] 
             ?? Environment.GetEnvironmentVariable("API_URL") 
             ?? (builder.Environment.IsDevelopment() ? "http://localhost:8000" : "http://burger-backend:8000");

Console.WriteLine($"🔗 Configurando API URL: {apiUrl}");

// ============================================
// HTTP CLIENTS
// ============================================

// HttpClient para AuthenticationService (sin handler, ya que el login no necesita token)
builder.Services.AddHttpClient<AuthenticationService>(client =>
{
    client.BaseAddress = new Uri(apiUrl);
    client.Timeout = TimeSpan.FromSeconds(30);
});

// ============================================
// AUTENTICACIÓN
// ============================================
// 1. AuthStateProvider gets a plain HttpClient (it doesn't need the JWT handler itself)
builder.Services.AddScoped(sp => 
{
    var localStorage = sp.GetRequiredService<Blazored.LocalStorage.ILocalStorageService>();
    var client = new HttpClient
    {
        BaseAddress = new Uri(apiUrl),
        Timeout = TimeSpan.FromSeconds(30)
    };
    return new AuthStateProvider(localStorage, client);
});

// 2. PosApiService gets a plain HttpClient and AuthStateProvider directly
//    Token is attached per-request inside PosApiService using the cached in-memory token.
//    This avoids the Blazor Server DelegatingHandler scoping issue entirely.
builder.Services.AddScoped(sp => 
{
    var authStateProvider = sp.GetRequiredService<AuthStateProvider>();
    
    var client = new HttpClient
    {
        BaseAddress = new Uri(apiUrl),
        Timeout = TimeSpan.FromSeconds(30)
    };
    
    var logger = sp.GetRequiredService<ILogger<PosApiService>>();
    return new PosApiService(client, logger, authStateProvider);
});
builder.Services.AddScoped<AuthenticationStateProvider>(provider => 
    provider.GetRequiredService<AuthStateProvider>());
builder.Services.AddCascadingAuthenticationState();
builder.Services.AddAuthentication(options =>
    {
        options.DefaultScheme = Microsoft.AspNetCore.Authentication.Cookies.CookieAuthenticationDefaults.AuthenticationScheme;
        options.DefaultChallengeScheme = Microsoft.AspNetCore.Authentication.Cookies.CookieAuthenticationDefaults.AuthenticationScheme;
    })
    .AddCookie(options =>
    {
        options.LoginPath = "/login";
        options.ExpireTimeSpan = TimeSpan.FromDays(1);
    });
builder.Services.AddAuthorization();

var app = builder.Build();

// Configure the HTTP request pipeline
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error");
    app.UseHsts();
}

app.UseStaticFiles();
app.UseAntiforgery();
app.UseAuthentication();
app.UseAuthorization();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

Console.WriteLine("✅ BurgerPOS Frontend iniciado correctamente");

app.Run();
