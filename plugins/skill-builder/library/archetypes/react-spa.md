# Archetype: React single-page app (<!-- fill: Vite / CRA -->)

**Applies to:** <!-- fill -->  ·  **Commands:** <!-- fill: package manager + dev/build/lint/test scripts -->

## How it flows
```
main.tsx -> providers (<!-- fill: router, query client, store, theme, i18n, auth -->) -> routes (<!-- fill: file and style -->)
  -> page component (<!-- fill: folder --> ) -> hooks (<!-- fill: React Query / SWR / custom -->) -> API client (<!-- fill: axios instance / fetch wrapper, base URL from env -->)
State: <!-- fill: server state vs client state rules -->   Styling: <!-- fill -->   Forms: <!-- fill -->
Auth: <!-- fill: token source/storage, guarded routes, 401 handling -->
```

## Rules for new code
<!-- fill from miner: folder structure (feature folders vs type folders), naming (PascalCase components, useX hooks), TS strictness,
component style (function components, props typing), data fetching through the shared client only, error/loading UI pattern,
i18n, accessibility, test location and style -->
- Never put secrets in `VITE_*` / `REACT_APP_*` variables: they are bundled into the browser.
- No `dangerouslySetInnerHTML` without sanitising (<!-- fill: library -->).

## Recipe: add-page
1. Page component in <!-- fill -->; 2. route entry in <!-- fill: router file -->; 3. navigation/menu <!-- fill -->;
4. data hook in <!-- fill --> calling the API client; 5. loading/error/empty states like <!-- fill: example page -->; 6. test <!-- fill -->.

## Recipe: add-component
<!-- fill: shared vs feature components folder, props/types, styling, story/test -->

## Recipe: add-api-call
1. Endpoint function in <!-- fill: api folder --> using <!-- fill: shared client -->; types for request/response;
2. hook wrapping it (<!-- fill: query keys convention, invalidation -->); 3. check the backend route exists:
`.ai/system/generated/contracts.md` → "Frontend -> backend calls"; if the backend is in another repo, note it in `overview.md`.
