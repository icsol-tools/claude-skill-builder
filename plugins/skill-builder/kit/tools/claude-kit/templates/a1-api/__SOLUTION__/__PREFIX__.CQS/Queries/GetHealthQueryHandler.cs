using __PREFIX__.CQS.Helpers;
using Dapper;
using Icsol.Common.Extensions;
using Icsol.GlobalizationResources.Resources;
using Icsol.Infrastructure.CQS.Queries;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.Localization;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace __PREFIX__.CQS.Queries
{
    /// <summary>
    /// Reference A1 query handler: Dapper read on a connection from IOptions&lt;ConnectionStrings&gt;,
    /// structured entry/exit logging, LogAndThrow with E781 on failure. Values always go in as parameters.
    /// </summary>
    public class GetHealthQueryHandler : IQueryHandler<GetHealthQuery, GetHealthResult>
    {
        private readonly ILogger<GetHealthQueryHandler> _logger;
        private readonly string _connectionString;
        private readonly IStringLocalizer<SharedResource> _localizer;

        public GetHealthQueryHandler(ILogger<GetHealthQueryHandler> logger,
                                     IOptions<ConnectionStrings> options,
                                     IStringLocalizer<SharedResource> localizer)
        {
            _logger = logger;
            _connectionString = options.Value.CommonConnectionString;
            _localizer = localizer;
        }

        public async Task<GetHealthResult> Execute(GetHealthQuery query)
        {
            _logger.LogInformation("Entering {Class}.{Method}", nameof(GetHealthQueryHandler), nameof(Execute));
            var result = new GetHealthResult { ServerTimeUtc = DateTime.UtcNow };
            try
            {
                await using var connection = new SqlConnection(_connectionString);
                await connection.OpenAsync();
                result.Database = await connection.ExecuteScalarAsync<int>("SELECT 1") == 1;
                query.IsSuccess = true;
            }
            catch (Exception ex)
            {
                _logger.LogAndThrow(ex, _localizer["E781"].Value, "E781");
            }
            finally
            {
                _logger.LogInformation("Exiting {Class}.{Method}", nameof(GetHealthQueryHandler), nameof(Execute));
            }
            return result;
        }
    }
}
