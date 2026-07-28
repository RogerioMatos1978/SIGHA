from django.contrib import admin

from .models import DisponibilidadeProfessor


@admin.register(DisponibilidadeProfessor)
class DisponibilidadeProfessorAdmin(admin.ModelAdmin):
    list_display = ('professor', 'dia_semana', 'horario', 'disponivel')
    list_filter = ('dia_semana', 'disponivel')
    search_fields = ('professor__nome',)
