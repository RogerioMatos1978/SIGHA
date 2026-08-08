"""
Camada de serviço do módulo Grade (Módulo 10).

Monta a estrutura usada pelo template para desenhar a tabela estilo Excel
(dias nas colunas, horários nas linhas) da grade de uma turma.
"""
from apps.disponibilidade.models import DiaSemana
from apps.horarios.models import Horario

from .models import Atribuicao, GradeAula


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


def atribuicoes_fora_do_vinculo(turma):
    """
    Atribuições ativas desta turma cujo professor não está autorizado a
    lecionar nela (Módulo 19: etapa de ensino + exceções por turma).
    Usado só para AVISAR o coordenador (na lista de atribuições e antes de
    gerar a grade automaticamente) — nunca para bloquear nada.
    """
    atribuicoes = (
        Atribuicao.objects.filter(turma=turma, ativo=True)
        .select_related('disciplina', 'professor')
        .prefetch_related('professor__turmas_liberadas', 'professor__turmas_bloqueadas')
    )
    return [a for a in atribuicoes if not a.professor.pode_lecionar_em(turma)]
