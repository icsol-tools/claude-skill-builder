# Archetype: dotnet-legacy-ba-da (Contoso.Billing, .NET Framework 4.8)

## How it flows
`Pages/*.aspx.cs` → `Contoso.Billing.BA/<Area>BA.cs` (business rules) → `Contoso.Billing.DA/<Area>DA.cs` (ADO.NET, stored procedures)
→ `Billing` DB. Shared helpers in `Contoso.Billing.Common/SqlHelper.cs`.

## Policy (confirmed): keep legacy, patch in place
Follow the existing BA/DA pattern for changes here. Do not introduce CQS or new frameworks into this unit.

## Rules for new code
- New DA methods call stored procedures through `SqlHelper.ExecuteDataTable(procName, params SqlParameter[])`. Never concatenate values
  into SQL, even though older methods do (`InvoiceDA.Search` - known risk, do not copy).
- BA methods validate input and throw `BillingException` with a message key from `App_GlobalResources/Messages.resx`.

## Recipe: legacy-change
1. Find the page and trace it: `.aspx.cs` event handler → BA method → DA method → procedure (`.ai/generated/db-objects.md`).
2. Change the lowest layer that owns the rule. Keep method signatures; add an overload if callers differ.
3. Procedure change → script in `db/changes/`, `ALTER PROCEDURE` guarded with `IF OBJECT_ID(...)`.
4. Build with `msbuild legacy/Contoso.Billing.sln /p:Configuration=Debug`; there are no tests - describe the manual check in the PR.
