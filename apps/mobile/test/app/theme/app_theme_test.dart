import 'package:aura_mobile/app/theme/app_theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('AppTheme', () {
    test('light color scheme matches design tokens', () {
      final theme = AppTheme.light;
      final scheme = theme.colorScheme;

      expect(scheme.primary, equals(const Color(0xFFFFC600)));
      expect(scheme.onPrimary, equals(const Color(0xFF041C2C)));
      expect(scheme.secondary, equals(const Color(0xFFAC4FC6)));
      expect(scheme.onSecondary, equals(const Color(0xFFFFFFFF)));
      expect(scheme.tertiary, equals(const Color(0xFF71DBD4)));
      expect(scheme.onTertiary, equals(const Color(0xFF041C2C)));
      // Background is deprecated; verify scaffold uses surface
      expect(theme.scaffoldBackgroundColor, equals(const Color(0xFFFFFFFF)));
      expect(scheme.surface, equals(const Color(0xFFFFFFFF)));
      expect(scheme.onSurface, equals(const Color(0xFF041C2C)));
      expect(scheme.outline, equals(const Color(0x33041C2C)));
    });

    test('dark color scheme matches design tokens', () {
      final theme = AppTheme.dark;
      final scheme = theme.colorScheme;

      expect(scheme.primary, equals(const Color(0xFF71DBD4)));
      expect(scheme.onPrimary, equals(const Color(0xFF041C2C)));
      expect(scheme.secondary, equals(const Color(0xFFAC4FC6)));
      expect(scheme.onSecondary, equals(const Color(0xFFFFFFFF)));
      expect(scheme.tertiary, equals(const Color(0xFFFFC600)));
      expect(scheme.onTertiary, equals(const Color(0xFF041C2C)));
      // Background is deprecated; verify scaffold uses surface
      expect(theme.scaffoldBackgroundColor, equals(const Color(0xFF0A2635)));
      expect(scheme.surface, equals(const Color(0xFF0A2635)));
      expect(scheme.onSurface, equals(const Color(0xFFFFFFFF)));
      expect(scheme.outline, equals(const Color(0x33FFFFFF)));
    });

    test('input decorations use outline and primary colors', () {
      final theme = AppTheme.light;
      final inputTheme = theme.inputDecorationTheme;
      final enabledBorder = inputTheme.enabledBorder! as OutlineInputBorder;
      final focusedBorder = inputTheme.focusedBorder! as OutlineInputBorder;

      expect(enabledBorder.borderSide.color, equals(theme.colorScheme.outline));
      expect(focusedBorder.borderSide.color, equals(theme.colorScheme.primary));
    });

    test('divider color follows outline token', () {
      final theme = AppTheme.dark;

      expect(theme.dividerTheme.color, equals(theme.colorScheme.outline));
    });
  });
}
