from django.contrib import admin

from .models import Professor


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'matricula', 'carga_horaria', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome', 'matricula', 'email')
