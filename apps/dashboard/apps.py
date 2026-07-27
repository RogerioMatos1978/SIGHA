from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """Configuração do app Dashboard — Módulo 3 do SIGHA."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    label = 'dashboard'
    verbose_name = 'Dashboard'
