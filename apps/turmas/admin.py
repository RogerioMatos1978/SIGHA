from django.contrib import admin

from .models import Turma


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'serie', 'turno', 'ativo')
    list_filter = ('turno', 'ativo')
    search_fields = ('nome', 'serie')
