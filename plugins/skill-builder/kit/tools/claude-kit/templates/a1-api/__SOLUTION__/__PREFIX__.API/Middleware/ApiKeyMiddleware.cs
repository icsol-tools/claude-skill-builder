using System.Security.Cryptography;
using System.Text;

namespace __PREFIX__.API.Middleware
{
    /// <summary>
    /// Default authentication for this API: callers send header X-Api-Key with one of the keys in
    /// configuration "Security:ApiKeys" (an array; set it with user-secrets or server environment variables,
    /// never in appsettings.json). Fails closed: with no keys configured, every protected request is rejected.
    /// Paths in "Security:AnonymousPaths" (default: /api/v1/health) and Swagger in Development are open.
    /// If this API must use a different scheme (e.g. a company token or OAuth),
    /// replace this middleware and record the decision in .ai/decisions.md.
    /// </summary>
    public class ApiKeyMiddleware
    {
        public const string HeaderName = "X-Api-Key";
        private readonly RequestDelegate _next;
        private readonly ILogger<ApiKeyMiddleware> _logger;
        private readonly byte[][] _keys;
        private readonly string[] _anonymousPaths;
        private readonly bool _isDevelopment;

        public ApiKeyMiddleware(RequestDelegate next, IConfiguration configuration, ILogger<ApiKeyMiddleware> logger, IWebHostEnvironment env)
        {
            _next = next;
            _logger = logger;
            _isDevelopment = env.IsDevelopment();
            _keys = (configuration.GetSection("Security:ApiKeys").Get<string[]>() ?? Array.Empty<string>())
                    .Where(k => !string.IsNullOrWhiteSpace(k))
                    .Select(k => Encoding.UTF8.GetBytes(k))
                    .ToArray();
            _anonymousPaths = configuration.GetSection("Security:AnonymousPaths").Get<string[]>() ?? new[] { "/api/v1/health" };
            if (_keys.Length == 0)
            {
                _logger.LogWarning("No Security:ApiKeys configured. All protected requests will be rejected with 401.");
            }
        }

        public async Task InvokeAsync(HttpContext context)
        {
            var path = context.Request.Path;
            bool isAnonymous = _anonymousPaths.Any(p => path.StartsWithSegments(p, StringComparison.OrdinalIgnoreCase))
                               || (_isDevelopment && path.StartsWithSegments("/swagger", StringComparison.OrdinalIgnoreCase));
            if (isAnonymous || IsValidKey(context.Request.Headers[HeaderName].ToString()))
            {
                await _next(context);
                return;
            }

            _logger.LogWarning("Rejected request without a valid {Header}. Path: {Path}", HeaderName, path.Value);
            context.Response.StatusCode = StatusCodes.Status401Unauthorized;
            context.Response.ContentType = "application/json";
            // same shape as the Icsol exception handler responses, so callers parse one format
            await context.Response.WriteAsync("{\"isSuccess\":false,\"errorList\":[{\"message\":\"Unauthorized\",\"code\":null,\"type\":\"unauthorized\"}],\"responseData\":null}");
        }

        private bool IsValidKey(string presented)
        {
            if (string.IsNullOrEmpty(presented) || _keys.Length == 0)
            {
                return false;
            }
            var bytes = Encoding.UTF8.GetBytes(presented);
            return _keys.Any(k => k.Length == bytes.Length && CryptographicOperations.FixedTimeEquals(k, bytes));
        }
    }
}
