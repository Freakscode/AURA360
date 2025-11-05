"""Pruebas para la lógica de cuotas por suscripción."""

from django.test import TestCase

from users.models import SubscriptionTier, UsageLedger, UsageQuota, AppUser
from users.services import check_quota, consume_quota, get_quota_snapshot, QuotaExceeded


class CheckQuotaTests(TestCase):
    """Verifica el comportamiento del helper check_quota."""

    def setUp(self):
        """Configura datos para cada test individual.
        
        Usamos setUp en lugar de setUpTestData porque la consulta a 
        SubscriptionTier necesita una conexión activa que pytest-django
        garantiza esté disponible en setUp (después del fixture de DB).
        """
        super().setUp()
        self.tiers = {tier.code: tier for tier in SubscriptionTier.objects.all()}

    def _user(self, tier_code: str, user_id: int = 1) -> AppUser:
        return AppUser(
            id=user_id,
            tier=tier_code,
            full_name=f"Test {tier_code}",
            email=f"{tier_code}@example.com",
        )

    def test_seeded_tiers_exist(self):
        self.assertSetEqual(
            set(self.tiers.keys()),
            {'free', 'core', 'plus', 'premium'},
        )

    def test_free_metabolic_report_monthly_limit(self):
        user = self._user('free', user_id=101)

        decision = check_quota(user, 'metabolic_report')
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.limit, 1)
        self.assertIsInstance(decision.quota, UsageQuota)

        consume_quota(user, 'metabolic_report')

        second = check_quota(user, 'metabolic_report')
        self.assertFalse(second.allowed)
        self.assertEqual(second.reason, 'quota_exceeded')
        self.assertEqual(second.remaining, 0)

    def test_core_realtime_unlimited(self):
        user = self._user('core', user_id=102)

        decision = check_quota(user, 'realtime_update')
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, 'unlimited_quota')
        self.assertIsNone(decision.limit)

    def test_plus_chatbot_daily_limit(self):
        user = self._user('plus', user_id=103)

        # Consumir límite completo de sesiones de chatbot
        for _ in range(20):
            consume_quota(user, 'chatbot_session')

        decision = check_quota(user, 'chatbot_session')
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, 'quota_exceeded')
        self.assertEqual(decision.remaining, 0)

    def test_premium_vector_search_unlimited(self):
        user = self._user('premium', user_id=104)

        decision = check_quota(user, 'vector_search')
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, 'unlimited_quota')

    def test_resource_without_quota_is_allowed(self):
        user = self._user('core', user_id=105)

        decision = check_quota(user, 'nonexistent_resource')
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, 'quota_not_defined')

    def test_consume_quota_records_metadata(self):
        user = self._user('core', user_id=106)
        result = consume_quota(user, 'metabolic_report', metadata={'source': 'test'})

        self.assertIsInstance(result.ledger, UsageLedger)
        self.assertEqual(result.ledger.metadata['source'], 'test')

    def test_consume_quota_raises_when_limit_reached(self):
        user = self._user('free', user_id=107)
        consume_quota(user, 'metabolic_report')

        with self.assertRaises(QuotaExceeded) as ctx:
            consume_quota(user, 'metabolic_report')

        self.assertEqual(ctx.exception.decision.reason, 'quota_exceeded')

    def test_quota_snapshot_reflects_consumption(self):
        user = self._user('free', user_id=108)
        consume_quota(user, 'metabolic_report')

        snapshot = get_quota_snapshot(user)
        report = next(item for item in snapshot if item.resource_code == 'metabolic_report')

        self.assertEqual(report.limit, 1)
        self.assertEqual(report.consumed, 1)
        self.assertEqual(report.remaining, 0)
