import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:aura_mobile/features/rbac/application/controllers/active_access_context_controller.dart';
import 'package:aura_mobile/features/rbac/application/providers/access_contexts_provider.dart';
import 'package:aura_mobile/features/rbac/domain/entities/access_context.dart';
import 'package:aura_mobile/features/rbac/domain/entities/institution.dart';
import 'package:aura_mobile/features/rbac/domain/entities/institution_membership.dart';
import 'package:aura_mobile/features/rbac/domain/entities/institution_role.dart';
import 'package:aura_mobile/features/user/domain/entities/billing_plan.dart';
import 'package:aura_mobile/features/user/domain/entities/global_role.dart';

Institution _institution(int id) {
  return Institution(
    id: id,
    name: 'Institución $id',
    slug: 'inst-$id',
    isHealthcare: true,
    businessTier: 'standard',
    metadata: const {},
    billingEmail: null,
    createdAt: DateTime.utc(2025, 1, 1),
    updatedAt: DateTime.utc(2025, 1, 2),
  );
}

InstitutionMembership _membership({
  required int id,
  required bool isPrimary,
  required InstitutionRole role,
}) {
  return InstitutionMembership(
    id: id,
    institutionId: id * 10,
    userId: 42,
    role: role,
    isPrimary: isPrimary,
    status: 'active',
    startedAt: DateTime.utc(2025, 1, 1),
    endedAt: null,
    institution: _institution(id * 10),
  );
}

AccessContext _institutionContext({
  required bool isPrimary,
  required InstitutionRole role,
}) {
  final membership = _membership(
    id: isPrimary ? 1 : 2,
    isPrimary: isPrimary,
    role: role,
  );
  return AccessContext.fromMembership(
    membership,
    globalRole: GlobalRole.profesionalSalud,
    billingPlan: BillingPlan.b2b2c,
  );
}

AccessContext _independentContext() {
  return AccessContext.independent(
    globalRole: GlobalRole.profesionalSalud,
    billingPlan: BillingPlan.individual,
  );
}

void main() {
  test('elige contexto institucional primario como activo inicial', () async {
    final contexts = <AccessContext>[
      _institutionContext(
        isPrimary: false,
        role: InstitutionRole.profesionalSalud,
      ),
      _institutionContext(
        isPrimary: true,
        role: InstitutionRole.adminInstitucion,
      ),
      _independentContext(),
    ];

    final container = ProviderContainer(
      overrides: [accessContextsProvider.overrideWith((ref) async => contexts)],
    );
    addTearDown(container.dispose);

    final active = await container.read(
      activeAccessContextControllerProvider.future,
    );

    expect(active, isNotNull);
    expect(active!.isInstitution, isTrue);
    expect(active.institutionRole, InstitutionRole.adminInstitucion);
    expect(active.isPrimary, isTrue);
  });

  test('cuando no hay contextos devuelve null', () async {
    final container = ProviderContainer(
      overrides: [
        accessContextsProvider.overrideWith(
          (ref) async => const <AccessContext>[],
        ),
      ],
    );
    addTearDown(container.dispose);

    final active = await container.read(
      activeAccessContextControllerProvider.future,
    );

    expect(active, isNull);
  });

  test('setActive actualiza el contexto seleccionado', () async {
    final contexts = <AccessContext>[
      _institutionContext(
        isPrimary: false,
        role: InstitutionRole.profesionalSalud,
      ),
      _independentContext(),
    ];

    final container = ProviderContainer(
      overrides: [accessContextsProvider.overrideWith((ref) async => contexts)],
    );
    addTearDown(container.dispose);

    final controller = container.read(
      activeAccessContextControllerProvider.notifier,
    );
    await controller.refresh();

    final independentContext = contexts.last;
    controller.setActive(independentContext);

    final state = container.read(activeAccessContextControllerProvider);

    expect(state, isA<AsyncData<AccessContext?>>());
    final data = (state as AsyncData<AccessContext?>).value;
    expect(data, equals(independentContext));
  });
}
