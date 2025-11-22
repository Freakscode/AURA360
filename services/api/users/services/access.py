"""Lógica de acceso y control de cuotas por suscripción."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from django.db.models import Sum
from django.utils import timezone

from users.models import (
    AppUser,
    QuotaPeriod,
    SubscriptionTier,
    UsageLedger,
    UsageQuota,
)


@dataclass
class QuotaDecision:
    """Resultado de la validación de una cuota."""

    allowed: bool
    reason: str
    remaining: Optional[int]
    limit: Optional[int]
    quota: Optional[UsageQuota]


@dataclass
class QuotaConsumption:
    """Resultado exitoso de registrar un consumo."""

    ledger: UsageLedger
    decision: QuotaDecision


class QuotaExceeded(Exception):
    """Excepción lanzada cuando una cuota se excede."""

    def __init__(self, decision: QuotaDecision):
        self.decision = decision
        super().__init__('Quota exceeded')


@dataclass
class QuotaStatus:
    """Estado agregado de una cuota para un usuario."""

    resource_code: str
    limit: Optional[int]
    period: str
    consumed: int
    remaining: Optional[int]
    unlimited: bool

    def as_dict(self) -> Dict[str, Optional[int]]:
        return {
            'resource_code': self.resource_code,
            'limit': self.limit,
            'period': self.period,
            'consumed': self.consumed,
            'remaining': self.remaining,
            'unlimited': self.unlimited,
        }


def check_quota(user: AppUser, resource_code: str, *, quantity: int = 1, at: Optional[datetime] = None) -> QuotaDecision:
    """Verifica si un usuario puede consumir un recurso específico."""

    if quantity <= 0:
        return QuotaDecision(True, 'no_quantity_requested', None, None, None)

    tier = SubscriptionTier.objects.filter(code=user.tier).first()
    if tier is None:
        return QuotaDecision(True, 'tier_not_configured', None, None, None)

    quota = UsageQuota.objects.filter(tier=tier, resource_code=resource_code).first()
    if quota is None:
        return QuotaDecision(True, 'quota_not_defined', None, None, None)

    if quota.limit is None or quota.period == QuotaPeriod.UNLIMITED:
        return QuotaDecision(True, 'unlimited_quota', None, None, quota)

    period_start = _get_period_start(at, quota.period)
    filters = {
        'user_id': user.pk,
        'resource_code': resource_code,
    }
    if period_start is not None:
        filters['occurred_at__gte'] = period_start

    consumed = (
        UsageLedger.objects.filter(**filters)
        .aggregate(total=Sum('amount'))
        .get('total')
        or 0
    )

    remaining = max(quota.limit - consumed, 0)
    if quantity > remaining:
        return QuotaDecision(False, 'quota_exceeded', remaining, quota.limit, quota)

    return QuotaDecision(True, 'quota_available', remaining - quantity, quota.limit, quota)


def consume_quota(
    user: AppUser,
    resource_code: str,
    *,
    quantity: int = 1,
    metadata: Optional[Dict[str, str]] = None,
    at: Optional[datetime] = None,
) -> QuotaConsumption:
    """Registra el consumo de un recurso, lanzando un error si se excede."""

    decision = check_quota(user, resource_code, quantity=quantity, at=at)
    if not decision.allowed:
        raise QuotaExceeded(decision)

    ledger = UsageLedger.objects.create(
        user_id=user.pk,
        resource_code=resource_code,
        amount=quantity,
        quota=decision.quota,
        metadata=metadata or {},
    )

    return QuotaConsumption(ledger=ledger, decision=decision)


def get_quota_snapshot(user: AppUser, *, at: Optional[datetime] = None) -> List[QuotaStatus]:
    """Devuelve un resumen de todas las cuotas del usuario."""

    tier = (
        SubscriptionTier.objects.filter(code=user.tier)
        .prefetch_related('quotas')
        .first()
    )
    if tier is None:
        return []

    snapshot: List[QuotaStatus] = []
    for quota in tier.quotas.all():
        period_start = _get_period_start(at, quota.period)
        filters = {
            'user_id': user.pk,
            'resource_code': quota.resource_code,
        }
        if period_start is not None:
            filters['occurred_at__gte'] = period_start

        consumed = (
            UsageLedger.objects.filter(**filters)
            .aggregate(total=Sum('amount'))
            .get('total')
            or 0
        )

        if quota.limit is None or quota.period == QuotaPeriod.UNLIMITED:
            snapshot.append(
                QuotaStatus(
                    resource_code=quota.resource_code,
                    limit=None,
                    period=quota.period,
                    consumed=consumed,
                    remaining=None,
                    unlimited=True,
                )
            )
            continue

        remaining = max(quota.limit - consumed, 0)

        snapshot.append(
            QuotaStatus(
                resource_code=quota.resource_code,
                limit=quota.limit,
                period=quota.period,
                consumed=consumed,
                remaining=remaining,
                unlimited=False,
            )
        )

    return snapshot


def _get_period_start(current_time: Optional[datetime], period: str) -> Optional[datetime]:
    """Calcula el inicio del periodo de consumo para una cuota."""

    if period == QuotaPeriod.UNLIMITED:
        return None

    now = current_time or timezone.now()
    now = timezone.make_aware(now) if timezone.is_naive(now) else now
    now = timezone.localtime(now)

    if period == QuotaPeriod.DAILY:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == QuotaPeriod.WEEKLY:
        start_of_week = now - timedelta(days=now.weekday())
        return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == QuotaPeriod.MONTHLY:
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return None
