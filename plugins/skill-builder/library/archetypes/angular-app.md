# Archetype: Angular app (<!-- fill: version, standalone components or NgModules -->)

**Applies to:** <!-- fill -->  ·  **Commands:** <!-- fill: ng serve/build/test/lint -->

## How it flows
```
main.ts / app.config.ts (<!-- fill: providers: router, HttpClient + interceptors, store -->) -> app.routes.ts (<!-- fill: lazy loadComponent/loadChildren -->)
  -> feature component -> service (<!-- fill: providedIn root? -->) -> HttpClient (<!-- fill: base URL from environment.ts, interceptors for auth/errors -->)
State: <!-- fill: NgRx / signals / services -->   Forms: <!-- fill: reactive forms -->   UI: <!-- fill: Angular Material / PrimeNG / Bootstrap -->
```

## Rules for new code
<!-- fill from miner: standalone vs module, folder-per-feature, naming (*.component.ts, *.service.ts), change detection, RxJS patterns
(async pipe, takeUntilDestroyed), typed forms, guards/interceptors, i18n, tests (Karma/Jest) -->
- `environment.ts` is bundled into the browser: no secrets there.
- No `bypassSecurityTrust*` / `[innerHTML]` with untrusted data.

## Recipe: add-feature-route
1. Component in `src/app/<feature>/` (<!-- fill: standalone --> ); 2. route in <!-- fill: app.routes.ts / feature routes --> (lazy);
3. guard if protected <!-- fill -->; 4. menu/navigation <!-- fill -->; 5. spec file like <!-- fill: example -->.

## Recipe: add-component
<!-- fill: shared folder, inputs/outputs or signals, styles, spec -->

## Recipe: add-api-call
1. Method in the feature service using HttpClient and `environment.<apiKey>`; typed models in <!-- fill -->;
2. error handling via <!-- fill: interceptor / catchError -->; 3. confirm the backend route (`.ai/system/generated/contracts.md`).
