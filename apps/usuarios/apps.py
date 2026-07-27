from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    """Configuração do app Usuários — Módulo 1 do SIGHA."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.usuarios'
    label = 'usuarios'
    verbose_name = 'Usuários'
