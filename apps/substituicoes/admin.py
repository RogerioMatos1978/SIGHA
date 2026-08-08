from django.contrib import admin

from .models import Substituicao


@admin.register(Substituicao)
class SubstituicaoAdmin(admin.ModelAdmin):
    list_display = ('aula', 'data', 'professor_substituto', 'aula_cancelada', 'criado_por')
    list_filter = ('aula_cancelada', 'data')
    search_fields = ('aula__turma__nome', 'professor_substituto__nome', 'motivo')
