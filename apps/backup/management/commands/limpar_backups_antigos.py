"""
Comando de gerenciamento para remover backups antigos (disco + histórico).
Útil para agendar junto do `backup_automatico`, evitando que o disco
encha de dumps de meses atrás.

Exemplo (cron, todo dia às 4h, um pouco depois do backup):
    0 4 * * * cd /caminho/do/projeto && python manage.py limpar_backups_antigos
"""
from django.core.management.base import BaseCommand

from apps.backup import services


class Command(BaseCommand):
    help = 'Remove backups mais antigos que BACKUP_RETENCAO_DIAS (ou --dias).'

    def add_arguments(self, parser):
        parser.add_argument('--dias', type=int, default=None, help='Sobrepõe BACKUP_RETENCAO_DIAS.')

    def handle(self, *args, **options):
        quantidade = services.limpar_backups_antigos(dias=options['dias'])
        self.stdout.write(self.style.SUCCESS(f'{quantidade} backup(s) removido(s).'))
