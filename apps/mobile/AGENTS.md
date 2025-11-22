# Repository Guidelines

## Project Structure & Module Organization
- `lib/main.dart` bootstraps the app via `lib/app/bootstrap.dart`.
- `lib/app/` hosts configuration layers (router, DI, localization, theming, observers, services).
- `lib/core/` centralizes infrastructure helpers for network, storage, error handling, and utilities (network clients, security services, result helpers, database adapters).
- `lib/features/` contains domain modules (`auth`, `rbac`, `mind`, `body`, `soul`, `user`) with their state, services, and UI.
- `lib/shared/` keeps cross-cutting widgets and design assets reused across features.
- `env/` stores environment definitions (`local.env` drives `--dart-define-from-file`).
- `supabase/` tracks CLI configuration and migrations; keep it in sync with the database.
- `docs/` captures focused guides (theming, database state, entity schemas). Reference them when touching those areas.
- `assets/icons|images|l10n/` store static resources; register updates in `pubspec.yaml`.
- Tests live in `test/` (unit/widget) and `integration_test/` (end-to-end flows that drive the router).

## Build, Test & Development Commands
- `flutter pub get` synchronizes Dart and Flutter dependencies.
- `flutter analyze` runs static analysis enforced by `flutter_lints`.
- `flutter test` executes unit and widget suites; add `--coverage` when validating coverage locally.
- `flutter run -d <device>` launches the app on an emulator or device for interactive QA.
- `flutter build apk --release` / `flutter build ios --release` produce distributable binaries.
- With the repository `tool/` directory on your `PATH` (`export PATH="$PWD/tool:$PATH"`), `flutter run dev` delegates to the helper that injects `.env` settings via `--dart-define-from-file`. Copy `env/local.env.example` to `env/local.env` with your Supabase values.
- `flutter run dev --lan [--lan-interface en0|...] [--lan-ip <addr>]` (or invoking `tool/run_dev.sh` directly) rewrites Supabase/Postgres endpoints with your LAN IP for physical devices, and will prompt for a target device when several are connected. Use `--list-devices` to inspect connected targets.

## Coding Style & Naming Conventions
- Format code with `dart format .`; maintain 2-space indentation and trailing commas on multiline arguments.
- Resolve all analyzer warnings before review; do not suppress rules without discussion.
- Files use `snake_case.dart`; classes, enums, typedefs use `PascalCase`; variables and functions use `camelCase`.
- Riverpod providers end with `Provider`; view widgets mirroring screens end with `Page` or `View`.
- Keep feature code co-located under its module to preserve the clean architecture boundaries.

## Testing Guidelines
- Mirror `lib/` paths under `test/` (e.g., `lib/features/auth` → `test/features/auth`).
- Use `flutter_test` and Riverpod testing helpers; prefer descriptive `group`/`test` names over numeric cases.
- Place integration scenarios in `integration_test/` using `testWidgets`; entry points should be named `<feature>_test.dart`.
- Target meaningful coverage for business rules and key UI flows before merging.

## Feature Notes
- `features/mind/`: incluye un mood tracker básico; `MoodTrackerController` trabaja con un repositorio en memoria y la UI (`MindPage`) lista registros y permite crear entradas con nivel, notas y etiquetas.
- `features/body/`: consolida actividad física, registro nutricional y descanso en `BodyDashboardController`; la página muestra resúmenes y hojas modales para añadir actividad, comidas y hábitos de sueño.
- `features/soul/`: `IkigaiController` gestiona un perfil IKIGAI editable con secciones por cuadrante y una declaración integrada en `SoulPage`.
- `features/user/`: `UserContextController` permite capturar datos personales y contexto psicosocial en `UserContextPage`; persiste de forma local mientras se define la integración con Supabase.

## Environment & Supabase Setup
- Copy `env/local.env.example` to `env/local.env` and keep Supabase/Postgres credentials current; `DATABASE_DRIVER` defaults to `postgres` for local Supabase stacks.
- The dev helper (via `flutter run dev` or `tool/run_dev.sh`) automatically loads defines from `env/local.env`; combine with `--lan` flags when serving devices outside the emulator loopback.
- New account creation (`/signup`) populates Supabase `auth.users` metadata (`full_name`, `age`, `gender`, `tier`)—ensure local env keys allow email password sign-ups so backend triggers sync `app_users`.
- Start the local stack with `supabase start` and manage schema via `supabase/migrations/`; the app targets the default `postgres` database.
- Session bootstrap now signs out on expired Supabase sessions so the user can re-authenticate cleanly.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat(app): …`, `fix(core): …`) as seen in Git history.
- Keep commits focused; avoid unrelated refactors or formatting noise.
- Before opening a PR, run `flutter analyze` and `flutter test`, and record the results in the description.
- Provide context, linked issues, and UI screenshots or screen captures when visual changes occur.
- Tag module owners when touching `core/`, shared infrastructure, or cross-feature contracts.

## Documentation & References
- `docs/theming.md` covers Material 3 setup and usage guidelines.
- `docs/database_state.md` details Supabase workflows (LAN overrides, session handling, migration tips).
- `docs/database/README.md` tracks `app_users` schema; keep it aligned when evolving user data.
