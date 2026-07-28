"""
Comando de gerenciamento para gerar um backup fora da tela web — pensado
para ser agendado via cron (Linux) ou Tarefas Agendadas (Windows), por
exemplo uma vez por dia de madrugada.

Exemplo (cron, todo dia às 3h):
    0 3 * * * cd /caminho/do/projeto && python manage.py backup_automatico
"""
from django.core.management.base import BaseCommand

from apps.backup import services


class Command(BaseCommand):
    help = 'Gera um novo backup do banco de dados (sem usuário associado).'

    def handle(self, *args, **options):
        try:
            registro = services.gerar_backup(usuario=None)
        except services.ErroDeBackup as erro:
            self.stderr.write(self.style.ERROR(f'Falha ao gerar backup: {erro}'))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(
            f'Backup gerado: {registro.nome_arquivo} ({registro.tamanho_legivel})'
        ))
