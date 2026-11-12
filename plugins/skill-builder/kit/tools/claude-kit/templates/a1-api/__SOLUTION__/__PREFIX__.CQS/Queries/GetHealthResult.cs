namespace __PREFIX__.CQS.Queries
{
    public class GetHealthResult
    {
        public string Service { get; set; } = "__SOLUTION__";
        public bool Database { get; set; }
        public DateTime ServerTimeUtc { get; set; }
    }
}
