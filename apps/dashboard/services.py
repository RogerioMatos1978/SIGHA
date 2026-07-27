"""
Camada de serviço do Dashboard (Módulo 3).

Mantemos toda a lógica de agregação de indicadores aqui, separada da view
(Responsabilidade Única / SOLID). Os módulos que ainda não existem
(Professores, Disciplinas, Turmas, Ambientes, Grade...) aparecem como
"indisponível" em vez de mostrar zero — zero sugeriria "cadastrado e
vazio", enquanto o correto aqui é "módulo ainda não implementado".

Conforme cada módulo futuro for criado, basta trocar a função
correspondente por uma consulta real ao seu modelo — o dashboard e o
template não precisam mudar.
"""
from django.apps import apps as django_apps
from django.db.models import Count

from apps.usuarios.models import Usuario


def _contar_modelo(app_label, nome_modelo):
    """
    Retorna a contagem de um modelo se o app já existir no projeto,
    ou None se o módulo ainda não foi implementado.
    """
    try:
        modelo = django_apps.get_model(app_label, nome_modelo)
    except LookupError:
        return None
    return modelo.objects.count()


def obter_indicadores_usuarios():
    """Indicadores do Módulo 1, sempre disponíveis (já implementado)."""
    total = Usuario.objects.count()
    ativos = Usuario.objects.filter(ativo=True, is_active=True).count()
    por_papel = list(
        Usuario.objects.values('papel').order_by('papel').annotate(quantidade=Count('id'))
    )
    return {
        'total': total,
        'ativos': ativos,
        'inativos': total - ativos,
        'por_papel': por_papel,
    }


def obter_cartoes_resumo():
    """
    Cartões principais do dashboard. 'valor' None = módulo futuro,
    o template mostra "em breve" nesse caso.
    """
    return [
        {'chave': 'professores', 'titulo': 'Professores', 'icone': 'bi-person-workspace',
         'valor': _contar_modelo('professores', 'Professor')},
        {'chave': 'disciplinas', 'titulo': 'Disciplinas', 'icone': 'bi-journal-bookmark-fill',
         'valor': _contar_modelo('disciplinas', 'Disciplina')},
        {'chave': 'turmas', 'titulo': 'Turmas', 'icone': 'bi-people-fill',
         'valor': _contar_modelo('turmas', 'Turma')},
        {'chave': 'ambientes', 'titulo': 'Ambientes', 'icone': 'bi-door-open-fill',
         'valor': _contar_modelo('ambientes', 'Ambiente')},
        {'chave': 'carga_horaria', 'titulo': 'Carga horária semanal', 'icone': 'bi-clock-history',
         'valor': None},
        {'chave': 'horarios_livres', 'titulo': 'Horários livres', 'icone': 'bi-calendar2-check',
         'valor': None},
        {'chave': 'conflitos', 'titulo': 'Conflitos encontrados', 'icone': 'bi-exclamation-triangle-fill',
         'valor': None},
    ]
