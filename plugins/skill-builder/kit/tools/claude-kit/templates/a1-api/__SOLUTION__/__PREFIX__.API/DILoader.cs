using __PREFIX__.API.Middleware;
using __PREFIX__.CQS.Helpers;
using Icsol.Common.Extensions;
using Icsol.GlobalizationResources.Extensions;
using Icsol.GlobalizationResources.Resources;
using Icsol.Infrastructure.CQS.Commands;
using Icsol.Infrastructure.CQS.Queries;
using Microsoft.OpenApi;
using NLog;
using System.Reflection;

namespace __PREFIX__.API
{
    /// <summary>
    /// All service registration and the HTTP pipeline for __SOLUTION__.
    /// Handlers are registered automatically from the CQS assembly; everything else is registered here by hand
    /// (see .ai/standards/icsol-cqs.md - Dependency injection).
    /// </summary>
    public class DILoader
    {
        private const string CqsAssembly = "__PREFIX__.CQS";
        private readonly IConfiguration _configuration;
        private readonly Logger _logger;

        public DILoader(IConfiguration configuration, Logger logger)
        {
            _configuration = configuration;
            _logger = logger;
        }

        public void ConfigureServices(IServiceCollection services)
        {
            AddCors(services);
            services.AddControllers().AddDataAnnotationsGlobalization();
            services.AddEndpointsApiExplorer();
            services.AddScoped<IQueryDispatcher, QueryDispatcher>();
            services.AddScoped<ICommandDispatcher, CommandDispatcher>();
            AddSwagger(services);
            AddConfigureModels(services);
            AddContexts(services);
            AddRepositories(services);
            AddCommandQueryHandlers(services, CqsAssembly);
        }

        public void Configure(WebApplication app)
        {
            if (app.Environment.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }
            app.UseCors("AllowedOrigin");
            app.ConfigureExceptionHandler<SharedResource>();
            app.UseGlobalizationHandler(null!);
            app.UseMiddleware<ApiKeyMiddleware>();
            app.UseAuthorization();
            app.MapControllers();

            if (app.Environment.IsDevelopment() || _configuration.GetValue<bool>("EnableSwagger"))
            {
                app.UseSwagger();
                app.UseSwaggerUI(c =>
                {
                    string basePath = string.IsNullOrWhiteSpace(c.RoutePrefix) ? "." : "..";
                    c.SwaggerEndpoint($"{basePath}/swagger/v1/swagger.json", "__SOLUTION__ API v1");
                });
            }

            app.Run();
        }

        // ---------------------------------------------------------------- registrations

        private void AddConfigureModels(IServiceCollection services)
        {
            services.AddOptions();
            services.Configure<ConnectionStrings>(_configuration.GetSection("ConnectionStrings"));
        }

        private void AddContexts(IServiceCollection services)
        {
            // EF Core contexts for writes, one per database, e.g.:
            // services.AddDbContext<SalesContext>(o => o.UseSqlServer(_configuration.GetConnectionString("SalesConnectionString")));
        }

        private void AddRepositories(IServiceCollection services)
        {
            // services.AddScoped<IRepository<Models.Enquiry>, EnquiryRepository>();
        }

        private void AddCommandQueryHandlers(IServiceCollection services, string assembly)
        {
            var cqs = Assembly.GetExecutingAssembly().GetReferencedAssemblies().FirstOrDefault(a => a.Name == assembly)
                      ?? throw new InvalidOperationException($"{assembly} is not referenced by the API project.");
            var types = Assembly.Load(cqs).GetTypes();

            foreach (var handler in types.Where(t => t.GetInterfaces().Any(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(ICommandHandler<>))))
            {
                services.AddScoped(handler.GetInterfaces().First(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(ICommandHandler<>)), handler);
            }
            foreach (var handler in types.Where(t => t.GetInterfaces().Any(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(IQueryHandler<,>))))
            {
                services.AddScoped(handler.GetInterfaces().First(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(IQueryHandler<,>)), handler);
            }
        }

        private void AddCors(IServiceCollection services)
        {
            // Explicit origins only. An empty list means no browser origin is allowed.
            var origins = _configuration.GetSection("Cors:AllowedOrigins").Get<string[]>() ?? Array.Empty<string>();
            services.AddCors(options => options.AddPolicy("AllowedOrigin", policy =>
            {
                if (origins.Length > 0)
                {
                    policy.WithOrigins(origins).AllowAnyHeader().AllowAnyMethod();
                }
            }));
        }

        private void AddSwagger(IServiceCollection services)
        {
            services.AddSwaggerGen(c =>
            {
                c.SwaggerDoc("v1", new OpenApiInfo { Title = "__SOLUTION__ API", Version = "v1" });
            });
        }
    }
}
