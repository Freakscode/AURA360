"""
Kafka integration for AURA360 Agents Service

Handles event-driven communication for Guardian requests and responses.
"""

from .handlers import GuardianRequestHandler

__all__ = ["GuardianRequestHandler"]
