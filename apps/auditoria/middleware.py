"""
Middleware do Módulo 16 (Auditoria).

Os sinais `post_save`/`post_delete` (usados para registrar quem criou,
alterou ou removeu um registro) não recebem o `request` — só a instância
do modelo. Este middleware guarda o usuário e o IP da requisição atual
numa variável local à thread, para que `signals.py` saiba quem fez cada
alteração sem precisar tocar em nenhuma view dos módulos anteriores.

Padrão equivalente ao usado por bibliotecas como django-crum.
"""
import threading

_local = threading.local()


def extrair_ip(request):
    encaminhado = request.META.get('HTTP_X_FORWARDED_FOR')
    if encaminhado:
        return encaminhado.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def obter_usuario_atual():
    return getattr(_local, 'usuario', None)


def obter_ip_atual():
    return getattr(_local, 'ip', None)


class UsuarioAtualMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.usuario = getattr(request, 'user', None)
        _local.ip = extrair_ip(request)
        try:
            return self.get_response(request)
        finally:
            _local.usuario = None
            _local.ip = None
