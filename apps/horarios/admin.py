from django.contrib import admin

from .models import Horario


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('ordem', 'inicio', 'fim', 'intervalo', 'ativo')
    list_filter = ('intervalo', 'ativo')
    ordering = ('ordem',)
