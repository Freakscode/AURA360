"""App configuration for papers."""

from django.apps import AppConfig


class PapersConfig(AppConfig):
    """Configuration for the papers app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'papers'
    verbose_name = 'Artículos Científicos'
