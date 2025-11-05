# Database State & Access Notes

## Local Supabase stack
- `supabase start` launches the CLI-managed containers. All services (Auth, PostgREST, Realtime, Storage) talk to the default database `postgres` on port `54322`.
- Running `supabase db reset` on the local project recreates `postgres` from the migration files under `supabase/migrations/`.
- We previously experimented with a secondary database (`aura`), but the stack resets it on every restart. The app now targets `postgres` again to stay aligned with Supabase defaults.
- Si generas claves ES256/RS256 con `supabase gen signing-key`, el JWKS público queda en `http://127.0.0.1:54321/auth/v1/.well-known/jwks.json`; apunta `SUPABASE_JWKS_URL` del backend a ese endpoint mientras trabajas en local.

## LAN testing from physical devices
- Once the repository `tool/` directory is on your `PATH` (`export PATH="$PWD/tool:$PATH"`), `flutter run dev --lan [--lan-interface en0|...]` invokes the helper script, auto-detects your machine IP, prompts for a target device when multiple are available, and rewrites the runtime defines:
  - `SUPABASE_URL=http://<LAN_IP>:54321`
  - `POSTGRES_HOST=<LAN_IP>`
  - `POSTGRES_PORT=54322`
  - `POSTGRES_DATABASE=postgres`
- You can still execute the helper directly (`tool/run_dev.sh`) if you prefer an explicit invocation or need to bypass the wrapper.
- The script no longer enforces or seeds an `aura` database; ensure the Supabase containers are running before launching the app.

## Session/bootstrap behaviour
- When the app fetches an `AppUser`, it first checks `public.app_users`. If the row is missing, it upserts via Supabase REST and, as a fallback, pulls from `auth.users` over Postgres.
- If Supabase returns an expired session while bootstrapping, the data source now signs out so the user can log in again.

## Applying migrations to remote environments
- Generate migrations locally with `supabase db commit` and keep them in version control.
- Deploy them with `supabase db push --db-url <postgresql://user:pass@host:port/db>` (use `--dry-run` first). Point the URL at the actual database name your remote project uses.
