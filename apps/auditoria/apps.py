from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    """Configuração do app Auditoria — Módulo 16 do SIGHA."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.auditoria'
    label = 'auditoria'
    verbose_name = 'Auditoria'

    def ready(self):
        from . import signals
        signals.conectar()
