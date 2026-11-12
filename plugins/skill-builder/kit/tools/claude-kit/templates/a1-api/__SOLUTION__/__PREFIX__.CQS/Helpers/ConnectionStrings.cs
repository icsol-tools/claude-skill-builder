namespace __PREFIX__.CQS.Helpers
{
    /// <summary>
    /// Bound to the "ConnectionStrings" section. Add one property per database this service uses,
    /// named exactly like the key in appsettings.json, and a matching entry in .ai/db-map.json.
    /// </summary>
    public class ConnectionStrings
    {
        public string CommonConnectionString { get; set; } = string.Empty;
    }
}
