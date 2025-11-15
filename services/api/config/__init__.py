"""Django config package exposing the Celery app."""
from .celery import app as celery_app

__all__ = ("celery_app",)
