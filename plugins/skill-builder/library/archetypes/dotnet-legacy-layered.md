# Archetype: legacy layered .NET (<!-- fill: BA/DA, BLL/DAL, Manager/Repository, DataTable -->)

**Applies to:** <!-- fill -->
**Team policy:** <!-- fill: keep legacy (patch in place) or migrate on touch --> (confirm)

## How it flows
```
<!-- fill: controller/page -> auth check -> business class (new'ed or DI) -> data class -> SQL/proc (how built) -> DataTable/DataSet -> JSON/view -->
```

## Rules for new code
- Follow the neighbouring code's structure; do not add new layers.
- SQL values are parameters even here: <!-- fill: the parameterised helper to add/use, e.g. an ExecuteProc(name, params) overload -->.
- <!-- fill: response format / status codes clients rely on, auth check to copy -->

## Recipe: legacy-change
1. Model/parameter class: <!-- fill: folder, naming suffix -->.
2. Business method in the area's existing class: <!-- fill -->.
3. Data call through the parameterised helper.
4. Controller/page action: copy the nearest one (auth check, logging, error → status mapping).
5. Proc change (if any): export current definition, `CREATE OR ALTER` script, keep result-set shape.
6. Don't revive commented-out code; don't edit designer/report binaries with Claude.
