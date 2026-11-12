# Archetype: Next.js app (<!-- fill: App Router / Pages Router / both -->)

**Applies to:** <!-- fill -->  ·  **Commands:** <!-- fill -->

## How it flows
```
app/ (or pages/) -> layout.tsx / _app.tsx (<!-- fill: providers -->) -> route segments (<!-- fill: groups, dynamic params -->)
Server components fetch with <!-- fill: fetch + cache/revalidate / server actions / route handlers --> ; client components ('use client') use <!-- fill: SWR / React Query -->
API: app/api/**/route.ts (or pages/api) -> <!-- fill: backend calls / DB -->
Env: NEXT_PUBLIC_* = browser-visible; everything else server-only.  Auth: <!-- fill: NextAuth / middleware.ts / cookies -->
```

## Rules for new code
<!-- fill from miner: server vs client component default, data fetching and caching rules, error.tsx/loading.tsx usage, metadata,
image/font handling, folder conventions, styling, tests -->
- Never read a non-`NEXT_PUBLIC_` env var in a `'use client'` file; never put secrets in `NEXT_PUBLIC_*`.
- Route handlers and server actions validate input (<!-- fill: zod? -->) and check auth.

## Recipe: add-page
1. `app/<segment>/page.tsx` (server component by default) + `loading.tsx` / `error.tsx` like <!-- fill: example -->;
2. data access via <!-- fill -->; 3. client parts split into `'use client'` components in <!-- fill -->; 4. navigation <!-- fill -->; 5. metadata.

## Recipe: add-api-route
1. `app/api/<path>/route.ts` exporting `GET`/`POST`...; 2. input validation + auth; 3. call backend/DB via <!-- fill -->;
4. typed response; 5. who calls it (frontend code) - update `overview.md`.

## Recipe: add-component
<!-- fill: components folder, server/client choice, styling, tests -->
