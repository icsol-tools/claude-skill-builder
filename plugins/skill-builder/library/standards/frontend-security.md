# Standard: frontend security

- No raw HTML from data: `dangerouslySetInnerHTML`, `[innerHTML]`, `v-html`, `bypassSecurityTrust*` only with a sanitiser
  (<!-- fill: DOMPurify / Angular DomSanitizer policy -->) and a comment saying why.
- No `eval` / `new Function` / string `setTimeout`.
- Tokens: <!-- fill: where auth tokens live (httpOnly cookie preferred over localStorage) and how 401/refresh is handled -->.
- All API calls go through the shared client (<!-- fill -->) so auth headers, base URL and error handling are consistent.
- Route guards are UX, not security: the backend must authorise every call.
- Dependencies: `npm audit --omit=dev` reviewed in verify; no packages from unknown registries.
