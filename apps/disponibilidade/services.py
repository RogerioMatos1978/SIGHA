"""
Lógica de negócio do módulo Disponibilidade, separada da view (SOLID).
"""
from apps.horarios.models import Horario

from .models import DiaSemana, DisponibilidadeProfessor


def horarios_da_grade():
    """Só entram na grade de disponibilidade os horários de aula ativos
    (intervalos não fazem sentido aqui — professor não "dá aula" no recreio)."""
    return Horario.objects.filter(ativo=True, intervalo=False).order_by('ordem')


def garantir_grade_completa(professor):
    """
    Garante que exista um registro de disponibilidade para cada combinação
    de dia da semana x horário deste professor (assumindo disponível por
    padrão na primeira vez). Sem isso, a tela de edição não teria o que
    exibir para um professor recém-cadastrado.
    """
    horarios = horarios_da_grade()
    existentes = set(
        DisponibilidadeProfessor.objects.filter(professor=professor)
        .values_list('dia_semana', 'horario_id')
    )
    novos = [
        DisponibilidadeProfessor(professor=professor, dia_semana=dia, horario=horario, disponivel=True)
        for dia, _ in DiaSemana.choices
        for horario in horarios
        if (dia, horario.id) not in existentes
    ]
    if novos:
        DisponibilidadeProfessor.objects.bulk_create(novos)


def montar_grade(professor):
    """Retorna a grade pronta para o template: dict {horario: {dia: registro}}."""
    garantir_grade_completa(professor)
    registros = (
        DisponibilidadeProfessor.objects.filter(professor=professor)
        .select_related('horario')
    )
    por_horario = {}
    for registro in registros:
        por_horario.setdefault(registro.horario, {})[registro.dia_semana] = registro
    return dict(sorted(por_horario.items(), key=lambda item: item[0].ordem))


def salvar_grade(professor, dados_post):
    """
    Atualiza disponibilidade a partir do POST do formulário em grade.
    Cada checkbox marcada como "disponível" é nomeada `disp_<horario_id>_<dia>`.
    """
    registros = DisponibilidadeProfessor.objects.filter(professor=professor)
    atualizados = []
    for registro in registros:
        campo = f'disp_{registro.horario_id}_{registro.dia_semana}'
        novo_valor = campo in dados_post
        if registro.disponivel != novo_valor:
            registro.disponivel = novo_valor
            atualizados.append(registro)
    if atualizados:
        DisponibilidadeProfessor.objects.bulk_update(atualizados, ['disponivel'])
