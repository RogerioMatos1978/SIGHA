from django.contrib import admin

from .models import Disciplina


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla', 'quantidade_aulas_semana', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome', 'sigla')
