"""
Filtros auxiliares de template do Calendário: cor do badge por tipo de
evento, e comparação de datas (o Django não compara `date` com facilidade
dentro do template sem um filtro próprio).
"""
from django import template

register = template.Library()

_CLASSE_POR_TIPO = {
    'FERIADO': 'bg-danger',
    'RECESSO': 'bg-secondary',
    'PROVA': 'bg-warning text-dark',
    'EVENTO': 'bg-primary',
    'REUNIAO': 'bg-info text-dark',
    'OUTRO': 'bg-dark',
}


@register.filter
def classe_badge_evento(tipo):
    return _CLASSE_POR_TIPO.get(tipo, 'bg-secondary')


@register.filter
def igual(data1, data2):
    return data1 == data2
