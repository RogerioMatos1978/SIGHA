"""
Camada de serviço do módulo Relatórios (Módulo 13).

Todos os relatórios são somente leitura: nenhuma função aqui grava nada
no banco. Isso deixa este módulo pronto para o próximo (Módulo 14 —
Exportações), que vai reaproveitar estas mesmas funções para gerar os
arquivos em Excel/PDF/Word em vez de recalcular tudo de novo.
"""
from collections import defaultdict

from apps.ambientes.models import Ambiente
from apps.disponibilidade.models import DiaSemana
from apps.grade.models import GradeAula
from apps.horarios.models import Horario
from apps.professores.models import Professor
from apps.turmas.models import Turma

DIAS_LETIVOS_POR_SEMANA = 5


def grade_semanal_do_professor(professor, ano_letivo, semestre):
    """
    Mesma estrutura usada na Grade visual por turma (Módulo 10), só que
    do ponto de vista do professor: em qual turma/disciplina/ambiente ele
    está em cada dia/horário da semana.
    """
    horarios = list(Horario.objects.filter(ativo=True, intervalo=False).order_by('ordem'))
    aulas = GradeAula.objects.filter(
        professor=professor, ano_letivo=ano_letivo, semestre=semestre,
    ).select_related('turma', 'disciplina', 'ambiente', 'horario')
    mapa = {(aula.dia_semana, aula.horario_id): aula for aula in aulas}

    grade = {}
    for horario in horarios:
        linha = {}
        for codigo_dia, _rotulo in DiaSemana.choices:
            linha[codigo_dia] = mapa.get((codigo_dia, horario.id))
        grade[horario] = linha
    return grade


def relatorio_carga_horaria(ano_letivo, semestre):
    """Para cada professor ativo: quantas aulas já tem no período vs a carga horária máxima."""
    aulas_por_professor = defaultdict(int)
    for aula in GradeAula.objects.filter(ano_letivo=ano_letivo, semestre=semestre).only('professor_id'):
        aulas_por_professor[aula.professor_id] += 1

    linhas = []
    for professor in Professor.objects.filter(ativo=True).order_by('nome'):
        alocadas = aulas_por_professor.get(professor.id, 0)
        maximo = professor.carga_horaria
        percentual = round((alocadas / maximo) * 100, 1) if maximo else 0
        linhas.append({
            'professor': professor, 'alocadas': alocadas, 'maximo': maximo,
            'livres': max(maximo - alocadas, 0), 'percentual': percentual,
        })
    return linhas


def relatorio_ocupacao_ambientes(ano_letivo, semestre):
    """Para cada ambiente ativo: quantas aulas o usam no período vs a capacidade total de slots."""
    horarios_ativos = Horario.objects.filter(ativo=True, intervalo=False).count()
    slots_por_unidade_capacidade = horarios_ativos * DIAS_LETIVOS_POR_SEMANA

    aulas_por_ambiente = defaultdict(int)
    for aula in GradeAula.objects.filter(ano_letivo=ano_letivo, semestre=semestre).only('ambiente_id'):
        aulas_por_ambiente[aula.ambiente_id] += 1

    linhas = []
    for ambiente in Ambiente.objects.filter(ativo=True).order_by('tipo', 'nome'):
        alocadas = aulas_por_ambiente.get(ambiente.id, 0)
        capacidade_total = slots_por_unidade_capacidade * ambiente.capacidade
        percentual = round((alocadas / capacidade_total) * 100, 1) if capacidade_total else 0
        linhas.append({
            'ambiente': ambiente, 'alocadas': alocadas, 'capacidade_total': capacidade_total,
            'percentual': percentual,
        })
    return linhas


def relatorio_pendencias_por_turma(ano_letivo, semestre):
    """
    Para cada turma com atribuições cadastradas (Módulo 10/11): quantas
    aulas ainda faltam encaixar na grade. Reaproveita a mesma conta que o
    algoritmo automático usa para decidir o que falta gerar.
    """
    from apps.algoritmo.solver import resumo_atribuicoes  # import local evita import circular no boot

    linhas = []
    for turma in Turma.objects.filter(ativo=True).order_by('serie', 'nome'):
        resumo = resumo_atribuicoes(turma, ano_letivo, semestre)
        if not resumo:
            continue
        necessarias = sum(item['necessarias'] for item in resumo)
        alocadas = sum(item['alocadas'] for item in resumo)
        faltantes = sum(item['faltantes'] for item in resumo)
        linhas.append({
            'turma': turma, 'necessarias': necessarias, 'alocadas': alocadas,
            'faltantes': faltantes, 'completa': faltantes == 0,
        })
    return linhas
