"""
Camada de serviço do módulo Grade (Módulo 10).

Monta a estrutura usada pelo template para desenhar a tabela estilo Excel
(dias nas colunas, horários nas linhas) da grade de uma turma.
"""
from apps.disponibilidade.models import DiaSemana
from apps.horarios.models import Horario

from .models import GradeAula


def horarios_da_grade():
    return Horario.objects.filter(ativo=True, intervalo=False).order_by('ordem')


def montar_grade_turma(turma, ano_letivo, semestre):
    """Retorna {horario: {codigo_dia: aula_ou_None}} para uma turma/período."""
    aulas = GradeAula.objects.filter(
        turma=turma, ano_letivo=ano_letivo, semestre=semestre,
    ).select_related('disciplina', 'professor', 'ambiente')
    mapa = {(aula.dia_semana, aula.horario_id): aula for aula in aulas}

    grade = {}
    for horario in horarios_da_grade():
        linha = {}
        for codigo_dia, _rotulo in DiaSemana.choices:
            linha[codigo_dia] = mapa.get((codigo_dia, horario.id))
        grade[horario] = linha
    return grade
