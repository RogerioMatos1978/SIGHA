from django.apps import AppConfig


class ProfessoresConfig(AppConfig):
    """Configuração do app Professores — Módulo 4 do SIGHA."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.professores'
    label = 'professores'
    verbose_name = 'Professores'
