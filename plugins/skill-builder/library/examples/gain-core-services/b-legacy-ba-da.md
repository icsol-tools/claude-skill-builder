# Archetype B: legacy BA/DA (Business Access / Data Access)

**Where:** most of Gain.MobileApp.Integrations (every controller marked "Legacy BA/DA" in
`generated/entry-points.md`). The code was migrated from .NET Framework to .NET 10 with its
structure kept.

**Team policy: legacy areas keep using the legacy pattern.** New endpoints in a legacy area and
changes to legacy endpoints follow this file. Do not convert an endpoint to CQS unless the task
asks for it. The one exception is SQL safety (below), which applies to every new or changed
statement.

## How a request flows

```
HTTP -> <Area>Controller (ControllerBase, attribute routes "api/<thing>")
          -> token check: VA.ValidateAccessTokenWithPhoneNo(phone, token) / validate.ValidateAccessTokenWithUsername(...)
             (headers "Authorization" and "phoneno")  -> 401 "Access token expired"
          -> new <Area>BA().<method>(model)
               -> DataFormat.CreateXML(model)            (model -> XML string)
               -> new DBConnection().ExecuteSQL("EXEC <Db>.dbo.<Proc> @Xml='...', ...", returntype)
                    returntype: 0 non-query, 2 scalar, 3 JSON string, 5 DataTable, 6 DataSet
          -> DataTable row[0]["success"] decides 200 vs 417
          -> DF.DataTableToJSONWithJavaScriptSerializer(DT) -> ContentResult(application/json)
Integration trigger: new CallRabbitMQWriter().CallMQWriter(processCode, subProcessCode, referenceSlno, ...)
                     -> HTTP POST to Common.API mqWriter (URL from config "CallRMQWriter")
```

Config is read statically through `AppSettingsDataAccess.GetValue("Key")` (initialised in
`Program.cs`). Logging uses the static `Logger` class in `BusinessAccess/Logger.cs` plus
`ILogger<T>` in controllers.

## Recipe: add or change a legacy endpoint (`/gain-dev:legacy-endpoint`)

1. **Model**: `Models/<Thing>_<Source>To<Target>_P.cs` (request; `_P` suffix = parameter model,
   e.g. `BikeEnquiry_IKMCToDMS_P`). Property names become XML element names, so they must match
   what the proc reads.
2. **BA method**: in the area's existing `BusinessAccess/<Area>BA.cs` (create the file only for a
   new area). Build the XML with `DF.CreateXML(model)` and call the proc through
   **`DBConnection.ExecuteProc`** with parameters (`.ai/standards/sql-safety.md`). Return a `DataTable`.
3. **Controller action**: copy the shape of the nearest action in the same controller: token
   check, try/catch with the `ModuleName | step | Start/Stop` log lines, the `success` column check,
   and a `ContentResult` with 200 or 417.
4. **Proc**: lives in the database. Export it with `tools/gain-docgen/export-db-objects.ps1`,
   change it in a script attached to the PR, and keep returning a `success` column (callers depend on it).
5. **Integration trigger** (if the change must reach Salesforce/SAP): call `CallRabbitMQWriter.CallMQWriter`
   with the ProcessCode / SubProcessCode configured in the mapper table. Don't publish to RabbitMQ directly.
6. **Docs**: run the generator, then update `overview.md` / `gotchas.md` if behaviour changed.

## Rules specific to B

- Keep each change inside the area's existing BA class. Don't add new shared "helper" layers.
- Match neighbouring code for response format and status codes (417 for business failure). Mobile
  clients parse these responses.
- Never add a new endpoint without the token check its neighbours use. `generated/entry-points.md`
  shows only a minority of legacy controllers calling a validator. Check how the rest are
  protected before copying one that has no check.
- Don't revive commented-out files or methods (`generated/overview.md` → Traps).
- Reports (`Report/*.rpt` Crystal, `ReportMS/*.rdlc`) are binary or designer files. Do not edit them
  with Claude. Describe the change for a developer to make in the designer.
