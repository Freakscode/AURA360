from django.apps import AppConfig


class BodyConfig(AppConfig):
    """Configura la aplicación Django para el dominio de hábitos corporales."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'body'
    verbose_name = 'Bienestar Corporal'

