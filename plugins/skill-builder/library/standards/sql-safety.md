# Standard: SQL safety

**Rule for every stack and archetype, legacy included: every value you add or change in a SQL call is passed as a parameter.**
Untouched lines don't have to be rewritten, but no new concatenated/interpolated SQL, and any statement you edit is converted.
`generated/contracts-and-risks.md` counts SQL built from values per unit; the kit-docs-check workflow fails a PR that adds any.

| Data access | Safe form |
|---|---|
| ADO.NET (`SqlCommand`) | `cmd.Parameters.Add("@Id", SqlDbType.Int).Value = id;` with `CommandType.StoredProcedure` for procs |
| Dapper | `conn.QueryAsync<T>("SELECT ... WHERE Id = @Id", new { id })`; procs: `commandType: CommandType.StoredProcedure` |
| EF Core raw SQL | `FromSqlInterpolated($"EXEC dbo.Proc @p = {value}")` / `ExecuteSqlInterpolatedAsync` (never `FromSqlRaw(string-built)`) |
| EF6 | `Database.SqlQuery<T>("EXEC dbo.Proc @p", new SqlParameter("@p", value))` |
| Legacy helper that takes a SQL string | add one parameterised overload next to it (`ExecuteProc(name, IDictionary<string, object?> parameters)`) and use it for new/changed calls |
| Node / Next.js route handlers | the driver's parameter placeholders (`@p`, `$1`, `?`) or the ORM; never template strings |

Never: build `ORDER BY` / column / table names from input (map from an allow-list); `sp_executesql` with concatenated text in procs
you add; skip this rule "for consistency with the file".
