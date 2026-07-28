from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Configuração do app API — Módulo 15 do SIGHA."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.api'
    label = 'api'
    verbose_name = 'API'
