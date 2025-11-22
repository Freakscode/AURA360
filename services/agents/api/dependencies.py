from __future__ import annotations

from functools import lru_cache

from services.holistic import HolisticAdviceService


@lru_cache(maxsize=1)
def _holistic_service() -> HolisticAdviceService:
    return HolisticAdviceService()


def get_holistic_service() -> HolisticAdviceService:
    return _holistic_service()


__all__ = ["get_holistic_service"]