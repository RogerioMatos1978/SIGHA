from django.contrib import admin

from .models import Evento


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'data_inicio', 'data_fim', 'afeta_aulas', 'ano_letivo')
    list_filter = ('tipo', 'afeta_aulas', 'ano_letivo')
    search_fields = ('titulo', 'descricao')
