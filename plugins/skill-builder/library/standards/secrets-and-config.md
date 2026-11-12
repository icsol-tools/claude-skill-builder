# Standard: secrets and configuration

- **No secrets in git**: passwords, connection strings with credentials, API keys, client secrets, private keys, tokens.
  - .NET Core: base `appsettings.json` holds every key with an **empty** value; local values via `dotnet user-secrets`; servers via
    environment variables (`Section__Key`) or a vault.
  - .NET Framework: `Web.config` in git holds keys without secret values; <!-- fill: transforms / server-side config / vault -->.
  - Frontend: anything in `VITE_*`, `REACT_APP_*`, `NEXT_PUBLIC_*`, Angular `environment*.ts` is shipped to every browser -
    never secrets. Server-side secrets only in Next.js server code / route handlers.
  - `.env` files with real values are never committed; commit `.env.example` with names only.
- Claude Code is denied reading secret files (`.claude/settings.json`). Never paste secrets into prompts or docs.
- Every key the code reads must be declared in the base config (empty for secrets); `generated/config.md` lists keys that are not.
- Found a secret in git: move it out, **rotate it** (it stays in history), then add the file to `.gitignore` if appropriate.
