"""
Sinais do Módulo 16 (Auditoria).

Cobre dois tipos de evento:

1) Criação/atualização/remoção dos modelos acadêmicos — via
   `post_save`/`post_delete`. Esse caminho funciona não importa por onde
   o dado foi alterado (tela web, admin do Django ou API do Módulo 15),
   sem precisar tocar em nenhuma view existente.
2) Login, logout e tentativa de login que falhou — via os sinais
   padrão do `django.contrib.auth`.

A auditoria nunca deve derrubar a operação principal: qualquer erro ao
gravar o registro é só logado, nunca propagado.
"""
import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_delete, post_save

from apps.ambientes.models import Ambiente
from apps.backup.models import RegistroBackup
from apps.calendario.models import Evento
from apps.disciplinas.models import Disciplina
from apps.disponibilidade.models import DisponibilidadeProfessor
from apps.grade.models import Atribuicao, GradeAula
from apps.horarios.models import Horario
from apps.professores.models import Professor
from apps.turmas.models import Turma
from apps.usuarios.models import Usuario

from .middleware import extrair_ip, obter_ip_atual, obter_usuario_atual
from .models import Acao, RegistroAuditoria

logger = logging.getLogger('sigha.auditoria')

MODELOS_AUDITADOS = [
    Usuario, Professor, Disciplina, Turma, Ambiente, Horario,
    DisponibilidadeProfessor, Atribuicao, GradeAula, Evento,
    # RegistroBackup: gerar/remover um backup (Módulo 17) também aparece
    # na Auditoria como CRIACAO/REMOCAO — a ação de RESTAURAR é diferente
    # (não cria/apaga essa linha) e é gravada explicitamente em
    # apps/backup/services.py, com a ação Acao.RESTAURACAO.
    RegistroBackup,
]


def _registrar(acao, **campos):
    try:
        RegistroAuditoria.objects.create(acao=acao, **campos)
    except Exception:
        logger.exception('Falha ao gravar registro de auditoria (ação=%s)', acao)


def _usuario_valido(usuario):
    if usuario is not None and getattr(usuario, 'is_authenticated', False):
        return usuario
    return None


def _ao_salvar(sender, instance, created, **kwargs):
    _registrar(
        Acao.CRIACAO if created else Acao.ATUALIZACAO,
        usuario=_usuario_valido(obter_usuario_atual()),
        modelo=sender.__name__,
        objeto_id=str(instance.pk),
        objeto_repr=str(instance)[:300],
        ip=obter_ip_atual(),
    )


def _ao_remover(sender, instance, **kwargs):
    _registrar(
        Acao.REMOCAO,
        usuario=_usuario_valido(obter_usuario_atual()),
        modelo=sender.__name__,
        objeto_id=str(instance.pk),
        objeto_repr=str(instance)[:300],
        ip=obter_ip_atual(),
    )


def _ao_logar(sender, request, user, **kwargs):
    _registrar(
        Acao.LOGIN, usuario=_usuario_valido(user), modelo='Usuario',
        objeto_id=str(user.pk), objeto_repr=str(user), ip=extrair_ip(request),
    )


def _ao_deslogar(sender, request, user, **kwargs):
    if user is None:
        return
    _registrar(
        Acao.LOGOUT, usuario=_usuario_valido(user), modelo='Usuario',
        objeto_id=str(user.pk), objeto_repr=str(user), ip=extrair_ip(request),
    )


def _ao_falhar_login(sender, credentials, request=None, **kwargs):
    _registrar(
        Acao.LOGIN_FALHOU, usuario=None, modelo='Usuario', objeto_id='',
        objeto_repr=credentials.get('username', ''),
        ip=extrair_ip(request) if request is not None else None,
    )


def conectar():
    """Chamado uma vez em `AuditoriaConfig.ready()`."""
    for modelo in MODELOS_AUDITADOS:
        post_save.connect(_ao_salvar, sender=modelo, dispatch_uid=f'auditoria_save_{modelo.__name__}')
        post_delete.connect(_ao_remover, sender=modelo, dispatch_uid=f'auditoria_delete_{modelo.__name__}')

    user_logged_in.connect(_ao_logar, dispatch_uid='auditoria_login')
    user_logged_out.connect(_ao_deslogar, dispatch_uid='auditoria_logout')
    user_login_failed.connect(_ao_falhar_login, dispatch_uid='auditoria_login_falhou')
