"""
Serviços do módulo Backup (Módulo 17): gerar, restaurar, listar e limpar
backups do banco de dados via `pg_dump`/`psql`.

Tanto a tela web (`views.py`) quanto os comandos de gerenciamento
(`management/commands/`, para quem quiser agendar via cron/Tarefas do
Windows) chamam exatamente estas mesmas funções — nenhuma lógica
duplicada, igual em todos os outros módulos do sistema.

Usa `django.db.connection.settings_dict` (não `settings.DATABASES`
diretamente) para pegar host/porta/usuário/banco, porque é isso que
reflete corretamente o banco realmente em uso — inclusive o banco de
teste (`test_sigha`) trocado pelo Django durante `manage.py test`.
"""
import logging
import os
import subprocess
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.utils import timezone

from .models import RegistroBackup

logger = logging.getLogger('sigha.backup')


class ErroDeBackup(Exception):
    """Erro ao gerar, restaurar ou remover um backup (ex.: pg_dump/psql falhou)."""


def _parametros_banco():
    cfg = connection.settings_dict
    return {
        'nome': cfg['NAME'],
        'usuario': cfg['USER'],
        'senha': cfg['PASSWORD'],
        'host': cfg['HOST'],
        'porta': str(cfg['PORT']),
    }


def _ambiente_com_senha(senha):
    ambiente = os.environ.copy()
    ambiente['PGPASSWORD'] = senha or ''
    return ambiente


def _usuario_valido(usuario):
    if usuario is not None and getattr(usuario, 'is_authenticated', False):
        return usuario
    return None


def gerar_backup(usuario=None):
    """Gera um novo dump do banco (SQL texto, com DROP/CREATE) e registra no histórico."""
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    db = _parametros_banco()
    # Sufixo aleatório (não só o timestamp) para nunca colidir, mesmo se
    # dois backups forem gerados no mesmo segundo (dois cliques seguidos,
    # ou o comando agendado rodando junto de um clique manual).
    nome_arquivo = f"sigha_{timezone.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}.sql"
    caminho = settings.BACKUP_DIR / nome_arquivo

    comando = [
        settings.PG_DUMP_BIN, '-h', db['host'], '-p', db['porta'], '-U', db['usuario'],
        '--clean', '--if-exists', '--no-owner', '--no-privileges',
        '-f', str(caminho), db['nome'],
    ]
    resultado = subprocess.run(comando, env=_ambiente_com_senha(db['senha']), capture_output=True, text=True)
    if resultado.returncode != 0:
        if caminho.exists():
            caminho.unlink()
        logger.error('pg_dump falhou: %s', resultado.stderr)
        raise ErroDeBackup(resultado.stderr.strip() or 'pg_dump falhou sem mensagem de erro.')

    return RegistroBackup.objects.create(
        nome_arquivo=nome_arquivo,
        tamanho_bytes=caminho.stat().st_size,
        criado_por=_usuario_valido(usuario),
    )


def restaurar_backup(registro, usuario=None, ip=None):
    """
    Restaura o banco a partir de um backup já existente. Ação destrutiva
    e irreversível — substitui os dados atuais pelos do momento do backup.
    Sempre grava um registro na Auditoria (Módulo 16), tenha dado certo
    ou não, porque é a ação mais sensível do sistema.
    """
    from apps.auditoria.models import Acao, RegistroAuditoria

    caminho = registro.caminho_arquivo()
    if not caminho.is_file():
        raise ErroDeBackup(f'Arquivo "{registro.nome_arquivo}" não foi encontrado no disco.')

    db = _parametros_banco()
    comando = [
        settings.PSQL_BIN, '-h', db['host'], '-p', db['porta'], '-U', db['usuario'],
        '-d', db['nome'], '-v', 'ON_ERROR_STOP=1', '-f', str(caminho),
    ]
    resultado = subprocess.run(comando, env=_ambiente_com_senha(db['senha']), capture_output=True, text=True)
    sucesso = resultado.returncode == 0

    descricao = f'Restauração a partir de "{registro.nome_arquivo}"'
    if not sucesso:
        descricao += ' (falhou)'
    RegistroAuditoria.objects.create(
        acao=Acao.RESTAURACAO,
        usuario=_usuario_valido(usuario),
        modelo='RegistroBackup',
        objeto_id=str(registro.pk),
        objeto_repr=descricao,
        ip=ip,
    )

    if not sucesso:
        logger.error('psql (restaurar) falhou: %s', resultado.stderr)
        raise ErroDeBackup(resultado.stderr.strip() or 'psql falhou ao restaurar sem mensagem de erro.')
    return True


def excluir_backup(registro):
    """Remove o arquivo do disco (se existir) e o registro do histórico."""
    caminho = registro.caminho_arquivo()
    if caminho.is_file():
        caminho.unlink()
    registro.delete()


def listar_backups():
    return RegistroBackup.objects.select_related('criado_por').all()


def limpar_backups_antigos(dias=None):
    """Remove (disco + histórico) os backups mais velhos que `dias` (padrão: BACKUP_RETENCAO_DIAS)."""
    dias = dias if dias is not None else settings.BACKUP_RETENCAO_DIAS
    limite = timezone.now() - timedelta(days=dias)
    antigos = list(RegistroBackup.objects.filter(criado_em__lt=limite))
    for registro in antigos:
        excluir_backup(registro)
    return len(antigos)
