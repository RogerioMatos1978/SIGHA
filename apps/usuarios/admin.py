from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Disponibiliza o modelo customizado no /admin/ para gestão avançada."""
    list_display = ('username', 'first_name', 'last_name', 'papel', 'matricula', 'ativo', 'is_staff')
    list_filter = ('papel', 'ativo', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'matricula', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('Dados do SIGHA', {'fields': ('matricula', 'telefone', 'papel', 'ativo')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Dados do SIGHA', {'fields': ('matricula', 'telefone', 'papel', 'ativo')}),
    )
