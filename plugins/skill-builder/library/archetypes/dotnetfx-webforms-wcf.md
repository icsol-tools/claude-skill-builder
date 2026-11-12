# Archetype: Web Forms / WCF on .NET Framework (<!-- fill -->)

**Applies to:** <!-- fill -->  ·  **Build:** MSBuild / Visual Studio.

## How it flows
<!-- fill: .aspx + code-behind events / .svc contracts -> business layer -> data -->

## Rules
- Patch in place; keep code-behind patterns; no designer-file edits by hand except the matching control declarations.
- SQL values are parameters. Add new files to the `.csproj`.
- WCF contract changes are breaking for every client: treat `[ServiceContract]`/`[DataContract]` changes as cross-unit contracts.

## Recipe: legacy-change
<!-- fill: page/control pattern, master page, session/auth checks, data access helper -->

## Recipe: add-wcf-operation
1. `[OperationContract]` on the interface (additive only); 2. implementation; 3. `[DataContract]` types (new members optional,
`Order` at the end); 4. binding/config in Web.config <!-- fill -->; 5. tell client owners (`change-contract`).
