from django.contrib import admin

from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('criado_em', 'usuario', 'acao', 'modelo', 'objeto_id', 'ip')
    list_filter = ('acao', 'modelo')
    search_fields = ('objeto_repr', 'usuario__username')
    readonly_fields = [f.name for f in RegistroAuditoria._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
