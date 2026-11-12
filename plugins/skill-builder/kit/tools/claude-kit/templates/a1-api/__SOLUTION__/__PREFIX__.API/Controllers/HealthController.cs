using __PREFIX__.CQS.Queries;
using Icsol.Common.ExceptionHelpers;
using Icsol.Common.Extensions;
using Icsol.Common.Helpers;
using Icsol.Common.Response;
using Icsol.GlobalizationResources.Resources;
using Icsol.Infrastructure.Common;
using Icsol.Infrastructure.CQS.Queries;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Localization;

namespace __PREFIX__.API.Controllers
{
    /// <summary>
    /// Reference A1 action: thin controller -> query dispatcher -> handler -> ApiResponseWrapper.
    /// New endpoints copy this shape (see the `{{PREFIX}}-add-endpoint` skill).
    /// </summary>
    [Route("api/v1")]
    [ApiController]
    public class HealthController : ControllerBase
    {
        private readonly ILogger<HealthController> _logger;
        private readonly IQueryDispatcher _queryDispatcher;
        private readonly IStringLocalizer<SharedResource> _localizer;

        public HealthController(ILogger<HealthController> logger,
                                IQueryDispatcher queryDispatcher,
                                IStringLocalizer<SharedResource> localizer)
        {
            _logger = logger;
            _queryDispatcher = queryDispatcher;
            _localizer = localizer;
        }

        /// <summary>Liveness plus a SELECT 1 against the common database.</summary>
        [HttpGet]
        [Route("health")]
        public async Task<IActionResult> GetHealth()
        {
            _logger.LogInformation("Entering {Class}.{Method}", nameof(HealthController), nameof(GetHealth));
            var response = new ApiResponse();
            try
            {
                var query = new GetHealthQuery();
                GetHealthResult result = await _queryDispatcher.HandleAsync<GetHealthQuery, GetHealthResult>(query);

                if (result == null)
                    throw new IcsolException(string.Format(_localizer["E741"], _localizer["Data"]), "E741", ExceptionType.INVALID_DATA_ERROR);

                response.AddData(result);
                response.IsSuccess = query.IsSuccess;
            }
            catch (Exception ex)
            {
                _logger.LogAndThrow(ex);
            }
            finally
            {
                _logger.LogInformation("Exiting {Class}.{Method}", nameof(HealthController), nameof(GetHealth));
            }
            return new ApiResponseWrapper<ApiResponse>(response, System.Net.HttpStatusCode.OK);
        }
    }
}
