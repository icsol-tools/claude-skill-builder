using __PREFIX__.API;
using NLog;
using NLog.Web;

var logger = LogManager.Setup()
                       .LoadConfigurationFromFile("NLog.config")
                       .GetCurrentClassLogger();
logger.Debug("init main");

try
{
    var builder = WebApplication.CreateBuilder(args);

    builder.Logging.ClearProviders();
    builder.Logging.SetMinimumLevel(Microsoft.Extensions.Logging.LogLevel.Debug);
    builder.Host.UseNLog();

    var diLoader = new DILoader(builder.Configuration, logger);
    diLoader.ConfigureServices(builder.Services);

    var app = builder.Build();
    diLoader.Configure(app);
}
catch (Exception ex)
{
    logger.Error(ex, "Error in init");
    throw;
}
finally
{
    LogManager.Shutdown();
}
