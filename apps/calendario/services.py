"""
Camada de serviço do Calendário (Módulo 12): monta a grade mensal (semanas
x dias) que o template desenha, e resume o que acontece num dia específico
(eventos cadastrados +, se for dia letivo, as aulas previstas naquele dia
da semana em qualquer turma).
"""
import calendar as calendario_padrao

from apps.disponibilidade.models import DiaSemana
from apps.grade.models import GradeAula

from .models import Evento

DIA_SEMANA_POR_WEEKDAY = {
    0: DiaSemana.SEGUNDA,
    1: DiaSemana.TERCA,
    2: DiaSemana.QUARTA,
    3: DiaSemana.QUINTA,
    4: DiaSemana.SEXTA,
}


def montar_mes(ano, mes):
    """
    Retorna uma lista de semanas (segunda a domingo); cada semana é uma
    lista de 7 dicts {'data', 'no_mes', 'eventos'}.
    """
    cal = calendario_padrao.Calendar(firstweekday=0)
    semanas_datas = cal.monthdatescalendar(ano, mes)
    primeiro_dia = semanas_datas[0][0]
    ultimo_dia = semanas_datas[-1][-1]

    candidatos = Evento.objects.filter(data_inicio__lte=ultimo_dia)
    eventos_relevantes = [evento for evento in candidatos if evento.fim_efetivo >= primeiro_dia]

    semanas = []
    for semana_datas in semanas_datas:
        semana = []
        for dia in semana_datas:
            eventos_do_dia = [e for e in eventos_relevantes if e.data_inicio <= dia <= e.fim_efetivo]
            semana.append({'data': dia, 'no_mes': dia.month == mes, 'eventos': eventos_do_dia})
        semanas.append(semana)
    return semanas


def resumo_do_dia(dia):
    """
    Eventos cadastrados no dia + (se for dia útil e não houver evento que
    afete as aulas) as aulas previstas naquele dia da semana, para
    qualquer turma, no ano letivo correspondente ao ano do dia.
    """
    candidatos = Evento.objects.filter(data_inicio__lte=dia)
    eventos = [evento for evento in candidatos if evento.fim_efetivo >= dia]
    ha_evento_que_afeta_aulas = any(evento.afeta_aulas for evento in eventos)

    dia_semana = DIA_SEMANA_POR_WEEKDAY.get(dia.weekday())
    dia_letivo = dia_semana is not None and not ha_evento_que_afeta_aulas

    aulas = []
    if dia_letivo:
        aulas = list(
            GradeAula.objects.filter(dia_semana=dia_semana, ano_letivo=dia.year)
            .select_related('turma', 'disciplina', 'professor', 'ambiente', 'horario')
            .order_by('horario__ordem', 'turma__nome')
        )

    return {'dia': dia, 'eventos': eventos, 'dia_letivo': dia_letivo, 'aulas': aulas}
