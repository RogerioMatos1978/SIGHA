from django.contrib import admin

from .models import RegistroBackup


@admin.register(RegistroBackup)
class RegistroBackupAdmin(admin.ModelAdmin):
    list_display = ('nome_arquivo', 'tamanho_legivel', 'criado_por', 'criado_em')
    readonly_fields = [f.name for f in RegistroBackup._meta.fields]

    def has_add_permission(self, request):
        # Gerar um backup exige rodar pg_dump de verdade — só pela tela
        # própria (/backup/), nunca criando a linha "a seco" pelo admin.
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Remover pelo admin apagaria só a linha, sem tirar o arquivo do
        # disco — use a tela própria, que chama services.excluir_backup().
        return False
