import 'package:flutter_test/flutter_test.dart';
import 'package:aura_mobile/features/auth/application/controllers/auth_controller.dart';
import 'package:aura_mobile/features/auth/domain/entities/auth_session.dart';
import 'package:aura_mobile/features/auth/domain/repositories/auth_repository.dart';

void main() {
  group('AuthController', () {
    test(
      'hydrates to authenticated when repository returns a session',
      () async {
        final repository = FakeAuthRepository()
          ..hydrateResult = const AuthSession(
            accessToken: 'token',
            userId: 'user-123',
          );

        final controller = AuthController(repository);
        addTearDown(controller.dispose);
        await pumpMicrotasks();

        expect(controller.state.isAuthenticated, isTrue);
        expect(controller.state.session?.userId, 'user-123');
      },
    );

    test('hydrates to unauthenticated when repository returns null', () async {
      final repository = FakeAuthRepository()..hydrateResult = null;

      final controller = AuthController(repository);
      addTearDown(controller.dispose);
      await pumpMicrotasks();

      expect(controller.state.isAuthenticated, isFalse);
    });

    test('hydrates to unauthenticated when repository throws', () async {
      final repository = FakeAuthRepository()
        ..hydrateError = Exception('hydrate failure');

      final controller = AuthController(repository);
      addTearDown(controller.dispose);
      await pumpMicrotasks();

      expect(controller.state.isAuthenticated, isFalse);
    });

    test('login updates state to authenticated on success', () async {
      final repository = FakeAuthRepository()
        ..hydrateResult = null
        ..loginResult = const AuthSession(
          accessToken: 'token',
          userId: 'user-123',
        );

      final controller = AuthController(repository);
      addTearDown(controller.dispose);
      await pumpMicrotasks();

      final success = await controller.login('email@example.com', 'password');

      expect(success, isTrue);
      expect(controller.state.isAuthenticated, isTrue);
      expect(repository.logoutCalled, isFalse);
    });

    test('login returns false when repository throws', () async {
      final repository = FakeAuthRepository()
        ..hydrateResult = null
        ..loginError = Exception('login failure');

      final controller = AuthController(repository);
      addTearDown(controller.dispose);
      await pumpMicrotasks();

      final success = await controller.login('email@example.com', 'password');

      expect(success, isFalse);
      expect(controller.state.isAuthenticated, isFalse);
    });

    test(
      'logout delegates to repository and sets state to unauthenticated',
      () async {
        final repository = FakeAuthRepository()
          ..hydrateResult = const AuthSession(
            accessToken: 'token',
            userId: 'user-123',
          );

        final controller = AuthController(repository);
        addTearDown(controller.dispose);
        await pumpMicrotasks();

        await controller.logout();

        expect(repository.logoutCalled, isTrue);
        expect(controller.state.isAuthenticated, isFalse);
      },
    );
  });
}

Future<void> pumpMicrotasks() async {
  await Future<void>.delayed(Duration.zero);
}

class FakeAuthRepository implements AuthRepository {
  AuthSession? hydrateResult;
  Object? hydrateError;
  AuthSession? loginResult;
  Object? loginError;
  AuthSession? signUpResult;
  Object? signUpError;
  bool logoutCalled = false;

  @override
  Future<AuthSession?> hydrate() async {
    if (hydrateError != null) {
      throw hydrateError!;
    }
    return hydrateResult;
  }

  @override
  Future<AuthSession> login({
    required String email,
    required String password,
  }) async {
    if (loginError != null) {
      throw loginError!;
    }
    final result = loginResult;
    if (result == null) {
      throw StateError('Stub loginResult before calling login');
    }
    return result;
  }

  @override
  Future<void> logout() async {
    logoutCalled = true;
  }

  @override
  Future<AuthSession> signUp({
    required String email,
    required String password,
    required String fullName,
    int? age,
    String? gender,
    String tier = 'free',
  }) async {
    if (signUpError != null) {
      throw signUpError!;
    }
    final result = signUpResult;
    if (result == null) {
      throw StateError('Stub signUpResult before calling signUp');
    }
    return result;
  }
}
