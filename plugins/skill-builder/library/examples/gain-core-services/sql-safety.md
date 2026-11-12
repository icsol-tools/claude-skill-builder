# Org standard: SQL safety

**Rule for all archetypes, legacy included: every value you add or change in a SQL call is
passed as a parameter.** You do not have to rewrite untouched lines, but you must not add
concatenated or interpolated SQL, and any statement you edit is converted.

Why: `generated/contracts-and-risks.md` in each solution counts SQL built from values. Several
of these endpoints are reachable by external systems and mobile apps. One `'` in a customer name
breaks the call, and a crafted value can run arbitrary SQL.

## A1 / A2: Dapper (reads, proc calls)

```csharp
// inline SQL
var row = await conn.QueryFirstOrDefaultAsync<DealerResult>(
    "SELECT DealerSlno FROM TSCommon.dbo.DealerMaster WHERE DealerCode = @DealerCode",
    new { query.DealerCode });

// stored procedure
var rows = await conn.QueryAsync<BookingResult>(
    "TSProduct.dbo.ProductSaleBooking_proc",
    new { p_BranchSlno = command.BranchSlno, p_CustomerName = command.CustomerName },
    commandType: CommandType.StoredProcedure);
```

Passing the query or command object itself (`conn.QueryAsync<T>(sql, query)`) is fine when its
property names match the `@parameters`.

## A1: EF raw SQL (observed in Gain.Integrations: `FromSqlRaw(sql.ToString())`)

Replace the string-built version with `FromSqlInterpolated`, which turns every `{value}` into a
parameter. It is nearly a drop-in replacement, so remove the quotes around values:

```csharp
// before (unsafe):  sql.Append($",@p_CustomerName = '{command.CustomerName}'"); ... FromSqlRaw(sql.ToString())
// after:
var result = await _context.BookingResponses.FromSqlInterpolated($@"
    EXECUTE TSProduct.dbo.ProductSaleBooking_proc
        @p_BranchSlno = {command.BranchSlno},
        @p_CustomerName = {command.CustomerName}").ToListAsync();
```

Dates: pass `DateTime?` values directly. Do not format them as strings.

## B (legacy BA/DA): `DBConnection`

Legacy code stays legacy (team policy), but new statements use the parameterised overload
`DBConnection.ExecuteProc`. If it does not exist yet in the solution, add it once, next to
`ExecuteSQL`, and use it from then on:

```csharp
public object ExecuteProc(string procName, IDictionary<string, object?> parameters, int returntype)
{
    string constr = AppSettingsDataAccess.GetConnectionString("Constring");
    using var con = new SqlConnection(constr);
    using var cmd = new SqlCommand(procName, con) { CommandType = CommandType.StoredProcedure };
    foreach (var p in parameters) cmd.Parameters.AddWithValue(p.Key, p.Value ?? DBNull.Value);
    con.Open();
    // same returntype contract as ExecuteSQL: 0 non-query, 2 scalar, 3 JSON, 5 DataTable, 6 DataSet
    ...
}
```

XML payloads (`DF.CreateXML(model)`) are passed as one parameter value, e.g. `["@LeadData"] = xml`.
They are never spliced into the SQL text.

## Never

- Build `ORDER BY`, column or table names from input. If one must vary, map it from an allow-list.
- Use `sp_executesql` with concatenated text inside procs you add.
- Disable this rule "for consistency with the file". Consistency doesn't override this rule.
