from django.contrib import admin

from .models import GradeAula


@admin.register(GradeAula)
class GradeAulaAdmin(admin.ModelAdmin):
    list_display = (
        'turma', 'dia_semana', 'horario', 'disciplina', 'professor',
        'ambiente', 'ano_letivo', 'semestre',
    )
    list_filter = ('ano_letivo', 'semestre', 'dia_semana', 'turma')
    search_fields = ('turma__nome', 'professor__nome', 'disciplina__nome')
