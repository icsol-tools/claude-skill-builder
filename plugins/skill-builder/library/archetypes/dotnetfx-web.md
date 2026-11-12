# Archetype: ASP.NET on .NET Framework (<!-- fill: Web API 2 / MVC 5 -->)

**Applies to:** <!-- fill -->
**Build:** MSBuild / Visual Studio (`dotnet build` cannot build most .NET Framework web projects). <!-- fill: exact command -->

## How it flows
```
IIS -> Global.asax / WebApiConfig / RouteConfig (<!-- fill: attribute routes with [RoutePrefix] or convention routes -->)
    -> <!-- fill: ApiController / Controller --> -> <!-- fill: DI container (Unity/Autofac/Ninject/none: new) -->
    -> <!-- fill: service / business layer --> -> <!-- fill: EF6 / Dapper / ADO / procs -->
Config: Web.config appSettings / connectionStrings via ConfigurationManager; transforms <!-- fill: Web.Release.config? -->
```

## Rules for new code
<!-- fill from miner: base controller, action filters (auth, logging, exception), response types (IHttpActionResult/ActionResult),
model binding/validation, async usage, packages.config vs PackageReference -->
- SQL values are parameters (`.ai/standards/sql-safety.md`).
- New .cs files must be added to the `.csproj` `<Compile Include>` list (old-style projects do not glob).
- Secrets: never in Web.config committed to git; <!-- fill: how the team handles them (transforms, server config, Key Vault) -->.

## Recipe: add-endpoint (Web API 2)
1. Model in <!-- fill -->; 2. data/business method <!-- fill -->; 3. action with `[HttpGet|Post]` + `[Route]` under the controller's
`[RoutePrefix]`; 4. add every new file to the `.csproj`; 5. register in DI if used <!-- fill -->; 6. copy from <!-- fill -->.

## Recipe: add-mvc-page (MVC 5)
1. Action + view model; 2. `Views/<Controller>/<Action>.cshtml` (layout <!-- fill -->); 3. bundle/script registration <!-- fill -->;
4. add files to the `.csproj`; 5. navigation/menu entry <!-- fill -->.
