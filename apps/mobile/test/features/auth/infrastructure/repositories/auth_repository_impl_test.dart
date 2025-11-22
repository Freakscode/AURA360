import 'package:flutter_test/flutter_test.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'package:aura_mobile/core/storage/secure_storage_service.dart';
import 'package:aura_mobile/features/auth/domain/entities/auth_session.dart';
import 'package:aura_mobile/features/auth/infrastructure/datasources/remote/auth_remote_data_source.dart';
import 'package:aura_mobile/features/auth/infrastructure/repositories/auth_repository_impl.dart';

void main() {
  group('AuthRepositoryImpl.login', () {
    test(
      'returns session and persists credentials when remote succeeds',
      () async {
        final remote = _FakeAuthRemoteDataSource()
          ..loginResult = const AuthSession(
            accessToken: 'access-token',
            refreshToken: 'refresh-token',
            userId: 'user-123',
          );
        final storage = _FakeSecureStorageService();
        final repository = AuthRepositoryImpl(remote, storage);

        final session = await repository.login(
          email: 'admin.sistema@aurademo.com',
          password: 'Aura360!',
        );

        expect(session.userId, 'user-123');
        expect(remote.loginInvocations, 1);
        expect(storage.writtenAccessToken, 'access-token');
        expect(storage.writtenUserId, 'user-123');
      },
    );

    test('propagates error when remote login throws', () async {
      final remote = _FakeAuthRemoteDataSource()
        ..loginError = Exception('invalid credentials');
      final storage = _FakeSecureStorageService();
      final repository = AuthRepositoryImpl(remote, storage);

      expect(
        () =>
            repository.login(email: 'paciente@aurademo.com', password: 'wrong'),
        throwsA(
          isA<Exception>().having(
            (error) => error.toString(),
            'message',
            contains('invalid credentials'),
          ),
        ),
      );
      expect(remote.loginInvocations, 1);
      expect(storage.writtenAccessToken, isNull);
      expect(storage.writtenUserId, isNull);
    });
  });

  group('AuthRepositoryImpl.hydrate', () {
    test('returns remote session when available and updates storage', () async {
      final remote = _FakeAuthRemoteDataSource()
        ..currentSessionResult = const AuthSession(
          accessToken: 'remote-token',
          refreshToken: 'remote-refresh',
          userId: 'user-456',
        );
      final storage = _FakeSecureStorageService();
      final repository = AuthRepositoryImpl(remote, storage);

      final session = await repository.hydrate();

      expect(session, isNotNull);
      expect(session!.userId, 'user-456');
      expect(storage.writtenAccessToken, 'remote-token');
      expect(storage.writtenUserId, 'user-456');
    });

    test(
      'falls back to cached credentials when remote has no session',
      () async {
        final remote = _FakeAuthRemoteDataSource()..currentSessionResult = null;
        final storage = _FakeSecureStorageService();
        await storage.writeAccessToken('cached-token');
        await storage.writeUserId('user-789');
        final repository = AuthRepositoryImpl(remote, storage);

        final session = await repository.hydrate();

        expect(session, isNotNull);
        expect(session!.accessToken, 'cached-token');
        expect(session.userId, 'user-789');
      },
    );

    test(
      'returns null when neither remote nor cache provide credentials',
      () async {
        final remote = _FakeAuthRemoteDataSource()..currentSessionResult = null;
        final storage = _FakeSecureStorageService();
        final repository = AuthRepositoryImpl(remote, storage);

        final session = await repository.hydrate();

        expect(session, isNull);
      },
    );
  });

  group('AuthRepositoryImpl.logout', () {
    test('delegates to remote and clears secure storage', () async {
      final remote = _FakeAuthRemoteDataSource();
      final storage = _FakeSecureStorageService();
      await storage.writeAccessToken('token');
      await storage.writeUserId('user');
      final repository = AuthRepositoryImpl(remote, storage);

      await repository.logout();

      expect(remote.logoutInvocations, 1);
      expect(storage.deletedAccessToken, isTrue);
      expect(storage.deletedUserId, isTrue);
    });
  });
}

class _FakeAuthRemoteDataSource extends AuthRemoteDataSource {
  _FakeAuthRemoteDataSource()
    : super(SupabaseClient('http://localhost', 'test-key'));

  AuthSession? loginResult;
  Object? loginError;
  AuthSession? signUpResult;
  Object? signUpError;
  AuthSession? currentSessionResult;
  final List<String> loginEmails = [];
  int loginInvocations = 0;
  int logoutInvocations = 0;

  @override
  Future<AuthSession> login({
    required String email,
    required String password,
  }) async {
    loginInvocations += 1;
    loginEmails.add(email);
    if (loginError != null) {
      throw loginError!;
    }
    final session = loginResult;
    if (session == null) {
      throw StateError('Stub loginResult before calling login');
    }
    return session;
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
    final session = signUpResult;
    if (session == null) {
      throw StateError('Stub signUpResult before calling signUp');
    }
    return session;
  }

  @override
  Future<void> logout() async {
    logoutInvocations += 1;
  }

  @override
  Future<AuthSession?> currentSession() async {
    return currentSessionResult;
  }
}

class _FakeSecureStorageService implements SecureStorageService {
  final Map<String, String?> _tokens = <String, String?>{};
  String? writtenAccessToken;
  String? writtenUserId;
  bool deletedAccessToken = false;
  bool deletedUserId = false;

  @override
  Future<void> writeAccessToken(String token) async {
    writtenAccessToken = token;
    _tokens['_access'] = token;
  }

  @override
  Future<String?> readAccessToken() async {
    return _tokens['_access'];
  }

  @override
  Future<void> deleteAccessToken() async {
    deletedAccessToken = true;
    _tokens['_access'] = null;
  }

  @override
  Future<void> writeUserId(String userId) async {
    writtenUserId = userId;
    _tokens['_user'] = userId;
  }

  @override
  Future<String?> readUserId() async {
    return _tokens['_user'];
  }

  @override
  Future<void> deleteUserId() async {
    deletedUserId = true;
    _tokens['_user'] = null;
  }
}
