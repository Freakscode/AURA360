"""Celery application configuration for the AURA365 backend."""
from __future__ import annotations

import os

from celery import Celery

# Ensure Django settings are loaded before Celery starts
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("aura365-api")

# Read configuration from Django settings using the CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from INSTALLED_APPS so each Django app can expose tasks.py
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Simple task to verify Celery wiring."""
    print(f"Request: {self.request!r}")
