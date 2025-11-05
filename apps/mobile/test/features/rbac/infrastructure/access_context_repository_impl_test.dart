import 'package:flutter_test/flutter_test.dart';

import 'package:aura_mobile/features/rbac/domain/entities/access_context.dart';
import 'package:aura_mobile/features/rbac/domain/entities/institution.dart';
import 'package:aura_mobile/features/rbac/domain/entities/institution_membership.dart';
import 'package:aura_mobile/features/rbac/domain/entities/institution_role.dart';
import 'package:aura_mobile/features/rbac/infrastructure/datasources/rbac_remote_data_source.dart';
import 'package:aura_mobile/features/rbac/infrastructure/repositories/access_context_repository_impl.dart';
import 'package:aura_mobile/features/user/domain/entities/app_user.dart';
import 'package:aura_mobile/features/user/domain/entities/billing_plan.dart';
import 'package:aura_mobile/features/user/domain/entities/global_role.dart';
import 'package:aura_mobile/features/user/domain/entities/user_tier.dart';

class FakeAccessControlDataSource implements AccessControlDataSource {
  FakeAccessControlDataSource({
    this.memberships = const <InstitutionMembership>[],
    this.independent = false,
  });

  List<InstitutionMembership> memberships;
  bool independent;

  @override
  Future<List<InstitutionMembership>> fetchMemberships(AppUser user) async {
    return memberships;
  }

  @override
  Future<bool> hasIndependentContext(AppUser user) async {
    return independent || user.isIndependent;
  }
}

Institution _institution({
  required int id,
  bool isHealthcare = false,
  String businessTier = 'standard',
}) {
  return Institution(
    id: id,
    name: 'Institución $id',
    slug: 'institucion-$id',
    isHealthcare: isHealthcare,
    businessTier: businessTier,
    metadata: const {},
    billingEmail: 'billing$id@example.com',
    createdAt: DateTime.utc(2025, 1, 1),
    updatedAt: DateTime.utc(2025, 1, 2),
  );
}

InstitutionMembership _membership({
  required int id,
  required int institutionId,
  required int userId,
  required InstitutionRole role,
  bool isPrimary = false,
  String status = 'active',
}) {
  return InstitutionMembership(
    id: id,
    institutionId: institutionId,
    userId: userId,
    role: role,
    isPrimary: isPrimary,
    status: status,
    startedAt: DateTime.utc(2025, 1, 1),
    endedAt: null,
    institution: _institution(id: institutionId, isHealthcare: true),
  );
}

AppUser _user({
  required String id,
  required int appUserId,
  required GlobalRole role,
  bool isIndependent = false,
  BillingPlan plan = BillingPlan.individual,
}) {
  return AppUser(
    id: id,
    appUserId: appUserId,
    email: '$id@example.com',
    tier: UserTier.premium,
    role: role,
    isIndependent: isIndependent,
    billingPlan: plan,
    createdAt: DateTime.utc(2025, 1, 1),
  );
}

void main() {
  group('AccessContextRepositoryImpl', () {
    test('crea contexto institucional para AdminInstitucion', () async {
      final dataSource = FakeAccessControlDataSource(
        memberships: [
          _membership(
            id: 1,
            institutionId: 10,
            userId: 5,
            role: InstitutionRole.adminInstitucion,
            isPrimary: true,
          ),
        ],
      );
      final repository = AccessContextRepositoryImpl(dataSource);
      final user = _user(
        id: 'user-admin',
        appUserId: 5,
        role: GlobalRole.adminInstitucion,
        plan: BillingPlan.institution,
      );

      final contexts = await repository.loadContexts(user);

      expect(contexts, hasLength(1));
      expect(contexts.first.type, AccessContextType.institution);
      expect(contexts.first.institutionRole, InstitutionRole.adminInstitucion);
    });

    test(
      'incluye práctica independiente para profesional con bandera',
      () async {
        final dataSource = FakeAccessControlDataSource(
          memberships: [
            _membership(
              id: 2,
              institutionId: 11,
              userId: 6,
              role: InstitutionRole.profesionalSalud,
              isPrimary: true,
            ),
          ],
          independent: true,
        );
        final repository = AccessContextRepositoryImpl(dataSource);
        final user = _user(
          id: 'user-prof',
          appUserId: 6,
          role: GlobalRole.profesionalSalud,
          plan: BillingPlan.b2b2c,
        );

        final contexts = await repository.loadContexts(user);

        expect(contexts, hasLength(2));
        expect(contexts.first.type, AccessContextType.institution);
        expect(contexts.last.type, AccessContextType.independent);
      },
    );

    test('Paciente solo recibe contexto institucional activo', () async {
      final dataSource = FakeAccessControlDataSource(
        memberships: [
          _membership(
            id: 3,
            institutionId: 12,
            userId: 7,
            role: InstitutionRole.paciente,
            isPrimary: true,
          ),
        ],
      );
      final repository = AccessContextRepositoryImpl(dataSource);
      final user = _user(
        id: 'user-patient',
        appUserId: 7,
        role: GlobalRole.paciente,
      );

      final contexts = await repository.loadContexts(user);

      expect(contexts, hasLength(1));
      expect(contexts.first.type, AccessContextType.institution);
      expect(contexts.first.institutionRole, InstitutionRole.paciente);
    });

    test('AdminSistema obtiene contexto independiente por defecto', () async {
      final dataSource = FakeAccessControlDataSource();
      final repository = AccessContextRepositoryImpl(dataSource);
      final user = _user(
        id: 'user-root',
        appUserId: 8,
        role: GlobalRole.adminSistema,
      );

      final contexts = await repository.loadContexts(user);

      expect(contexts, hasLength(1));
      expect(contexts.first.type, AccessContextType.independent);
    });

    test(
      'si no hay memberships se crea contexto independiente primario',
      () async {
        final dataSource = FakeAccessControlDataSource();
        final repository = AccessContextRepositoryImpl(dataSource);
        final user = _user(
          id: 'user-standalone',
          appUserId: 9,
          role: GlobalRole.general,
        );

        final contexts = await repository.loadContexts(user);

        expect(contexts, hasLength(1));
        expect(contexts.first.type, AccessContextType.independent);
        expect(contexts.first.isPrimary, isTrue);
      },
    );
  });
}
