from django.apps import AppConfig


class GradeConfig(AppConfig):
    """Configuração do app Grade — Módulo 10 do SIGHA."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.grade'
    label = 'grade'
    verbose_name = 'Grade'
