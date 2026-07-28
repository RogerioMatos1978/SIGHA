"""
Motor de geração automática da Grade (Módulo 11), usando OR-Tools (CP-SAT).

O que o solver decide: QUANDO (dia da semana + horário) cada aula de cada
atribuição (turma + disciplina + professor, cadastrada no Módulo 10) deve
acontecer, respeitando as mesmas regras que o preenchimento manual da
grade já respeita:

- a turma nunca fica com duas aulas no mesmo horário;
- o professor nunca é escalado num horário em que já dá aula para OUTRA
  turma (olhando a grade inteira da escola no período, não só desta turma);
- o professor nunca é escalado num horário que ele marcou como
  indisponível (Módulo 9);
- o professor nunca ultrapassa a própria carga horária semanal (Módulo 4);
- evita concentrar aulas da mesma disciplina no mesmo dia.

O QUE ambiente cada aula usa é decidido depois, de forma gulosa (greedy):
para cada aula já posicionada no tempo, escolhe o primeiro ambiente ativo
compatível com o tipo exigido pela disciplina que ainda tiver capacidade
de uso simultâneo livre naquele dia/horário — a mesma regra de capacidade
que `GradeAula.clean()` aplica no Módulo 10.

O solver NUNCA grava nada no banco: ele devolve uma lista de propostas
(dicionários com turma/disciplina/professor/dia_semana/horario/ambiente)
que a view tenta salvar uma a uma através de `GradeAula.full_clean()`,
reaproveitando — sem duplicar — toda a validação de conflito já construída
no Módulo 10. Isso garante que, mesmo se houver algum caso extremo que o
solver não previu, nenhuma aula inválida chega a ser persistida.
"""
from collections import defaultdict

from ortools.sat.python import cp_model

from apps.ambientes.models import Ambiente, TipoAmbiente
from apps.disponibilidade.models import DiaSemana, DisponibilidadeProfessor
from apps.grade.models import Atribuicao, GradeAula
from apps.horarios.models import Horario

MAX_AULAS_MESMA_DISCIPLINA_POR_DIA = 2
TEMPO_MAXIMO_SOLVER_SEGUNDOS = 15


def _aulas_ja_alocadas(turma, ano_letivo, semestre):
    """Quantas aulas de cada disciplina já existem na grade desta turma/período."""
    contagem = defaultdict(int)
    for aula in GradeAula.objects.filter(turma=turma, ano_letivo=ano_letivo, semestre=semestre).only('disciplina_id'):
        contagem[aula.disciplina_id] += 1
    return contagem


def resumo_atribuicoes(turma, ano_letivo, semestre):
    """
    Lista, para a tela de confirmação, quantas aulas cada atribuição ainda
    precisa (sem rodar o solver) — útil para o coordenador ver de antemão
    o que falta antes de clicar em "gerar".
    """
    ja_alocadas = _aulas_ja_alocadas(turma, ano_letivo, semestre)
    resumo = []
    for atribuicao in Atribuicao.objects.filter(turma=turma, ativo=True).select_related('disciplina', 'professor'):
        necessarias = atribuicao.disciplina.quantidade_aulas_semana
        alocadas = ja_alocadas.get(atribuicao.disciplina_id, 0)
        resumo.append({
            'atribuicao': atribuicao,
            'disciplina': atribuicao.disciplina,
            'professor': atribuicao.professor,
            'necessarias': necessarias,
            'alocadas': alocadas,
            'faltantes': max(necessarias - alocadas, 0),
        })
    return resumo


def gerar_propostas_para_turma(turma, ano_letivo, semestre):
    """
    Roda o CP-SAT e devolve:
        {
            'propostas': [{'turma','disciplina','professor','dia_semana','horario','ambiente'}, ...],
            'incompletas': [{'disciplina','professor','faltantes'}, ...],
            'sem_ambiente': [{'disciplina','professor','dia_semana','horario'}, ...],
        }
    Não salva nada no banco.
    """
    horarios = list(Horario.objects.filter(ativo=True, intervalo=False).order_by('ordem'))
    dias = [codigo for codigo, _rotulo in DiaSemana.choices]
    slots = [(dia, horario) for dia in dias for horario in horarios]

    atribuicoes = list(
        Atribuicao.objects.filter(turma=turma, ativo=True, disciplina__ativo=True, professor__ativo=True)
        .select_related('disciplina', 'professor')
    )
    if not atribuicoes or not slots:
        return {'propostas': [], 'incompletas': [], 'sem_ambiente': []}

    ja_alocadas = _aulas_ja_alocadas(turma, ano_letivo, semestre)

    aulas_existentes_turma = list(GradeAula.objects.filter(turma=turma, ano_letivo=ano_letivo, semestre=semestre))
    slots_ocupados_turma = {(a.dia_semana, a.horario_id) for a in aulas_existentes_turma}

    slots_ocupados_professor = defaultdict(set)
    aulas_professor_periodo = defaultdict(int)
    for aula in GradeAula.objects.filter(ano_letivo=ano_letivo, semestre=semestre).only(
        'professor_id', 'dia_semana', 'horario_id'
    ):
        slots_ocupados_professor[aula.professor_id].add((aula.dia_semana, aula.horario_id))
        aulas_professor_periodo[aula.professor_id] += 1

    professores_envolvidos = [a.professor_id for a in atribuicoes]
    indisponivel = defaultdict(set)
    for disponibilidade in DisponibilidadeProfessor.objects.filter(
        disponivel=False, professor_id__in=professores_envolvidos,
    ):
        indisponivel[disponibilidade.professor_id].add((disponibilidade.dia_semana, disponibilidade.horario_id))

    modelo = cp_model.CpModel()
    variaveis = {}
    necessarias = {}
    slots_validos_por_atribuicao = {}

    for atribuicao in atribuicoes:
        necessario = atribuicao.disciplina.quantidade_aulas_semana - ja_alocadas.get(atribuicao.disciplina_id, 0)
        necessarias[atribuicao.id] = max(necessario, 0)
        validos = []
        for idx, (dia, horario) in enumerate(slots):
            if (dia, horario.id) in slots_ocupados_turma:
                continue
            if (dia, horario.id) in slots_ocupados_professor.get(atribuicao.professor_id, set()):
                continue
            if (dia, horario.id) in indisponivel.get(atribuicao.professor_id, set()):
                continue
            validos.append(idx)
        slots_validos_por_atribuicao[atribuicao.id] = validos
        for idx in validos:
            variaveis[(atribuicao.id, idx)] = modelo.NewBoolVar(f'atrib{atribuicao.id}_slot{idx}')

    # 1) Nenhuma atribuição agenda mais aulas do que ainda precisa.
    for atribuicao in atribuicoes:
        termos = [variaveis[(atribuicao.id, idx)] for idx in slots_validos_por_atribuicao[atribuicao.id]]
        if termos:
            modelo.Add(sum(termos) <= necessarias[atribuicao.id])

    # 2) A turma não pode ter duas aulas no mesmo horário (entre as atribuições geradas agora).
    for idx in range(len(slots)):
        termos = [variaveis[(a.id, idx)] for a in atribuicoes if (a.id, idx) in variaveis]
        if len(termos) > 1:
            modelo.Add(sum(termos) <= 1)

    # 3) No máximo duas aulas da mesma disciplina no mesmo dia (evita concentrar tudo).
    for atribuicao in atribuicoes:
        por_dia = defaultdict(list)
        for idx in slots_validos_por_atribuicao[atribuicao.id]:
            dia, _horario = slots[idx]
            por_dia[dia].append(idx)
        for indices_do_dia in por_dia.values():
            if len(indices_do_dia) > MAX_AULAS_MESMA_DISCIPLINA_POR_DIA:
                modelo.Add(
                    sum(variaveis[(atribuicao.id, idx)] for idx in indices_do_dia)
                    <= MAX_AULAS_MESMA_DISCIPLINA_POR_DIA
                )

    # 4) Carga horária do professor: soma de tudo que ele já tem no período mais o
    #    que for agendado agora (em todas as atribuições dele nesta turma) não
    #    pode passar da carga horária semanal cadastrada no Módulo 4.
    atribuicoes_por_professor = defaultdict(list)
    for atribuicao in atribuicoes:
        atribuicoes_por_professor[atribuicao.professor_id].append(atribuicao)
    for professor_id, lista_atribuicoes in atribuicoes_por_professor.items():
        professor = lista_atribuicoes[0].professor
        ja_no_periodo = aulas_professor_periodo.get(professor_id, 0)
        restante = max(professor.carga_horaria - ja_no_periodo, 0)
        termos = [
            variaveis[(a.id, idx)]
            for a in lista_atribuicoes
            for idx in slots_validos_por_atribuicao[a.id]
        ]
        if termos:
            modelo.Add(sum(termos) <= restante)

    todas_variaveis = list(variaveis.values())
    if todas_variaveis:
        modelo.Maximize(sum(todas_variaveis))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TEMPO_MAXIMO_SOLVER_SEGUNDOS

    propostas = []
    incompletas = []

    if not todas_variaveis:
        for atribuicao in atribuicoes:
            if necessarias[atribuicao.id] > 0:
                incompletas.append({
                    'disciplina': atribuicao.disciplina, 'professor': atribuicao.professor,
                    'faltantes': necessarias[atribuicao.id],
                })
        return {'propostas': [], 'incompletas': incompletas, 'sem_ambiente': []}

    status = solver.Solve(modelo)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for atribuicao in atribuicoes:
            agendadas = 0
            for idx in slots_validos_por_atribuicao[atribuicao.id]:
                if solver.Value(variaveis[(atribuicao.id, idx)]):
                    dia, horario = slots[idx]
                    propostas.append({
                        'turma': turma, 'disciplina': atribuicao.disciplina, 'professor': atribuicao.professor,
                        'dia_semana': dia, 'horario': horario,
                    })
                    agendadas += 1
            faltantes = necessarias[atribuicao.id] - agendadas
            if faltantes > 0:
                incompletas.append({
                    'disciplina': atribuicao.disciplina, 'professor': atribuicao.professor, 'faltantes': faltantes,
                })
    else:
        for atribuicao in atribuicoes:
            if necessarias[atribuicao.id] > 0:
                incompletas.append({
                    'disciplina': atribuicao.disciplina, 'professor': atribuicao.professor,
                    'faltantes': necessarias[atribuicao.id],
                })

    # Escolhe o ambiente de cada proposta de forma gulosa, respeitando capacidade.
    ocupacao_ambiente = defaultdict(int)
    for aula in GradeAula.objects.filter(ano_letivo=ano_letivo, semestre=semestre).only(
        'ambiente_id', 'dia_semana', 'horario_id'
    ):
        ocupacao_ambiente[(aula.ambiente_id, aula.dia_semana, aula.horario_id)] += 1

    sem_ambiente = []
    propostas_completas = []
    for proposta in propostas:
        tipo_desejado = proposta['disciplina'].tipo_ambiente or TipoAmbiente.SALA
        candidatos = Ambiente.objects.filter(ativo=True, tipo=tipo_desejado).order_by('nome')
        chave_base = (proposta['dia_semana'], proposta['horario'].id)
        ambiente_escolhido = None
        for candidato in candidatos:
            ocupados = ocupacao_ambiente[(candidato.id, *chave_base)]
            if ocupados < candidato.capacidade:
                ambiente_escolhido = candidato
                break
        if ambiente_escolhido is None:
            sem_ambiente.append({
                'disciplina': proposta['disciplina'], 'professor': proposta['professor'],
                'dia_semana': proposta['dia_semana'], 'horario': proposta['horario'],
            })
            continue
        ocupacao_ambiente[(ambiente_escolhido.id, *chave_base)] += 1
        proposta['ambiente'] = ambiente_escolhido
        propostas_completas.append(proposta)

    return {'propostas': propostas_completas, 'incompletas': incompletas, 'sem_ambiente': sem_ambiente}
