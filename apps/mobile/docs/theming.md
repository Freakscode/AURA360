# Theming

The application theme is defined under `lib/app/theme/` and provides a fully custom Material 3 setup matching the Aura palette.

## Key files
- `app_colors.dart`: central color tokens for light and dark palettes.
- `app_theme.dart`: builds `ColorScheme` objects and shared `ThemeData` configuration.
- `theme_controller.dart`: Riverpod `StateNotifier` that exposes the active `ThemeMode` and helper methods to cycle/update it.

## Using the theme
- Widgets should prefer `Theme.of(context).colorScheme` to access semantic colors (e.g. `primary`, `outline`).
- Surface elements such as cards or inputs already receive the correct background and border via the shared subthemes. Prefer `FilledButton`, `OutlinedButton`, and `TextFormField` without overriding colors.
- When an explicit status color is required (errors, success, warnings), read it from the color scheme (`colorScheme.error`, etc.). Avoid hardcoded hex values.

## Theme mode
- `themeModeProvider` can be read/watched to reflect the current `ThemeMode`.
- To toggle between modes, call `ref.read(themeModeProvider.notifier).cycleThemeMode()` or `setThemeMode(ThemeMode.light/dark/system)` from presentation logic.
- Persistence is stubbed with a TODO and can be wired to the storage services when available.

## Migration tips
- Replace usages of `Colors.*` or raw hex values with the semantic colors from the scheme.
- Prefer existing `Divider`, `AppBar`, and `Card` widgets without custom styling—the theme already injects outline, surface, and tint defaults.
- Run `flutter analyze` and `flutter test` after migrating screens to ensure the style changes stay covered.
