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

Módulo 20: trocamos o gráfico "Usuários por papel" por um painel de
"Planejamento de hoje" — mais útil no dia a dia do coordenador do que um
gráfico decorativo, e vira o atalho principal do dashboard para quem quer
saber rapidamente o que tem agendado hoje sem entrar em cada tela.
"""
from django.apps import apps as django_apps
from django.db.models import Count, Q
from django.utils import timezone

from apps.usuarios.models import Usuario

# Índice de `date.weekday()` (Python: segunda=0 ... domingo=6) para o
# código de DiaSemana usado na Grade (Módulo 10) — mesma tabela usada em
# apps/substituicoes/models.py para validar a data de uma substituição.
_DIA_SEMANA_POR_WEEKDAY = {
    0: 'SEGUNDA', 1: 'TERCA', 2: 'QUARTA', 3: 'QUINTA', 4: 'SEXTA',
}


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


def _indicadores_da_grade():
    """
    A partir do Módulo 10 (Grade), calculamos estes três indicadores com
    dados reais em vez de "Em breve":

    - carga_horaria: total de aulas já encaixadas na grade no ano corrente
      (proxy simples da carga horária semanal ocupada em toda a escola).
    - horarios_livres: quantos espaços turma×horário×dia ainda estão vagos,
      considerando as turmas ativas e os horários de aula cadastrados.
    - conflitos: sempre 0 — as regras de `GradeAula.clean()` e as
      constraints do banco impedem que qualquer conflito chegue a ser
      salvo, então "conflitos encontrados" é um número real, não um chute.

    Se o módulo de Grade ainda não existir (projeto rodando com uma versão
    mais antiga do banco), os três voltam a aparecer como "Em breve".
    """
    try:
        GradeAula = django_apps.get_model('grade', 'GradeAula')
        Turma = django_apps.get_model('turmas', 'Turma')
        Horario = django_apps.get_model('horarios', 'Horario')
    except LookupError:
        return {'carga_horaria': None, 'horarios_livres': None, 'conflitos': None}

    ano_atual = timezone.now().year
    carga_horaria = GradeAula.objects.filter(ano_letivo=ano_atual).count()

    turmas_ativas = Turma.objects.filter(ativo=True).count()
    horarios_ativos = Horario.objects.filter(ativo=True, intervalo=False).count()
    total_slots = turmas_ativas * horarios_ativos * 5  # 5 dias letivos (segunda a sexta)
    horarios_livres = max(total_slots - carga_horaria, 0)

    return {'carga_horaria': carga_horaria, 'horarios_livres': horarios_livres, 'conflitos': 0}


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
    indicadores_grade = _indicadores_da_grade()
    return [
        {'chave': 'professores', 'titulo': 'Professores', 'icone': 'bi-person-workspace',
         'valor': _contar_modelo('professores', 'Professor')},
        {'chave': 'disciplinas', 'titulo': 'Disciplinas', 'icone': 'bi-journal-bookmark-fill',
         'valor': _contar_modelo('disciplinas', 'Disciplina')},
        {'chave': 'turmas', 'titulo': 'Turmas', 'icone': 'bi-people-fill',
         'valor': _contar_modelo('turmas', 'Turma')},
        {'chave': 'ambientes', 'titulo': 'Ambientes', 'icone': 'bi-door-open-fill',
         'valor': _contar_modelo('ambientes', 'Ambiente')},
        {'chave': 'carga_horaria', 'titulo': 'Aulas na grade (ano atual)', 'icone': 'bi-clock-history',
         'valor': indicadores_grade['carga_horaria']},
        {'chave': 'horarios_livres', 'titulo': 'Horários livres', 'icone': 'bi-calendar2-check',
         'valor': indicadores_grade['horarios_livres']},
        {'chave': 'conflitos', 'titulo': 'Conflitos encontrados', 'icone': 'bi-exclamation-triangle-fill',
         'valor': indicadores_grade['conflitos']},
    ]


def obter_planejamento_do_dia():
    """
    Painel "hoje" do dashboard (Módulo 20): aulas da grade e eventos do
    calendário que caem na data de hoje, para o coordenador ver de
    cara o que está agendado sem precisar abrir a grade de cada turma.

    Segue o mesmo padrão de "ano letivo + 1º semestre por padrão" usado
    em todo o resto do sistema (Grade, Algoritmo automático) — não tenta
    adivinhar o semestre atual a partir do mês, porque essa divisão é
    escolhida por quem lança a grade, não calculada.
    """
    hoje = timezone.localdate()
    dia_semana_hoje = _DIA_SEMANA_POR_WEEKDAY.get(hoje.weekday())

    resultado = {
        'data': hoje, 'dia_semana_hoje': dia_semana_hoje, 'e_dia_letivo': dia_semana_hoje is not None,
        'aulas': [], 'eventos': [],
    }

    try:
        GradeAula = django_apps.get_model('grade', 'GradeAula')
        Evento = django_apps.get_model('calendario', 'Evento')
    except LookupError:
        return resultado

    ano_atual = hoje.year
    if dia_semana_hoje:
        resultado['aulas'] = list(
            GradeAula.objects.filter(
                dia_semana=dia_semana_hoje, ano_letivo=ano_atual, semestre='1',
            )
            .select_related('turma', 'disciplina', 'professor', 'horario')
            .order_by('horario__ordem', 'turma__nome')
        )

    # Eventos que caem hoje: de um dia só (data_inicio == hoje) ou de
    # vários dias em que hoje está dentro do intervalo [data_inicio, data_fim].
    resultado['eventos'] = list(
        Evento.objects.filter(ano_letivo=ano_atual).filter(
            Q(data_inicio=hoje) | Q(data_inicio__lte=hoje, data_fim__gte=hoje)
        ).order_by('tipo')
    )
    return resultado
