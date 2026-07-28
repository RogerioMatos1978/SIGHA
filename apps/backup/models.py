"""
Modelo do módulo Backup (Módulo 17): cada linha é um dump do banco de
dados já gerado (arquivo .sql em `settings.BACKUP_DIR`). O arquivo em si
não fica no banco — só o registro de quando/quem gerou, para a tela de
histórico e para a Auditoria (Módulo 16) rastrear quem fez o quê.
"""
from django.conf import settings
from django.db import models


class RegistroBackup(models.Model):
    nome_arquivo = models.CharField('Nome do arquivo', max_length=255, unique=True)
    tamanho_bytes = models.BigIntegerField('Tamanho (bytes)', default=0)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Gerado por',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='backups_gerados',
        help_text='Em branco quando gerado pelo comando agendado (sem usuário logado).',
    )
    criado_em = models.DateTimeField('Data/hora', auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Backup'
        verbose_name_plural = 'Backups'

    def __str__(self):
        return self.nome_arquivo

    @property
    def tamanho_legivel(self):
        tamanho = float(self.tamanho_bytes)
        for unidade in ('B', 'KB', 'MB', 'GB'):
            if tamanho < 1024:
                return f'{tamanho:.1f} {unidade}'
            tamanho /= 1024
        return f'{tamanho:.1f} TB'

    def caminho_arquivo(self):
        return settings.BACKUP_DIR / self.nome_arquivo

    def existe_no_disco(self):
        return self.caminho_arquivo().is_file()
