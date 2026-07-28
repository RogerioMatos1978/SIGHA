"""
Filtro auxiliar de template: o Django não resolve `dicionario.variavel`
quando a chave vem de uma variável (só funciona com string literal), então
precisamos deste filtro para buscar a aula por dia da semana na grade.
"""
from django import template

register = template.Library()


@register.filter
def get_item(dicionario, chave):
    return dicionario.get(chave)
