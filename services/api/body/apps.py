from django.apps import AppConfig


class BodyConfig(AppConfig):
    """Configura la aplicación Django para el dominio de hábitos corporales."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'body'
    verbose_name = 'Bienestar Corporal'

    def ready(self):
        """
        Importa signals cuando la aplicación inicia.

        Esto registra los handlers de post_save para:
        - BodyMeasurement → cálculos automáticos
        - NutritionPlan → vectorización automática
        """
        import body.signals  # noqa: F401

