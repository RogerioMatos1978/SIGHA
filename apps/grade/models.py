"""
Modelo de Grade (Módulo 10).

Uma linha de GradeAula representa uma aula real, encaixada na grade de uma
turma: em tal dia da semana, em tal horário, tal disciplina é dada por tal
professor em tal ambiente — dentro de um ano letivo e semestre.

As regras obrigatórias da especificação são todas validadas em `clean()`
(ou por constraint do próprio banco), então nenhum caminho do sistema
(formulário, admin, futura API) consegue salvar uma aula em conflito:

1. Turma não pode ter duas aulas ao mesmo tempo (constraint do banco).
2. Professor não pode estar em duas turmas ao mesmo tempo (constraint do banco).
3. Ambiente respeita sua capacidade de uso simultâneo (validado em clean(),
   pois depende de contar quantas aulas já usam aquele ambiente).
4. Professor respeita a própria disponibilidade cadastrada (Módulo 9).
5. Professor não pode ultrapassar a própria carga horária semanal.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.ambientes.models import Ambiente
from apps.disciplinas.models import Disciplina
from apps.disponibilidade.models import DiaSemana, DisponibilidadeProfessor
from apps.horarios.models import Horario
from apps.professores.models import Professor
from apps.turmas.models import Turma


def ano_letivo_padrao():
    return timezone.now().year


class Semestre(models.TextChoices):
    PRIMEIRO = '1', '1º Semestre'
    SEGUNDO = '2', '2º Semestre'


class GradeAula(models.Model):
    turma = models.ForeignKey(
        Turma, verbose_name='Turma', on_delete=models.CASCADE, related_name='aulas',
    )
    disciplina = models.ForeignKey(
        Disciplina, verbose_name='Disciplina', on_delete=models.PROTECT, related_name='aulas',
    )
    professor = models.ForeignKey(
        Professor, verbose_name='Professor', on_delete=models.PROTECT, related_name='aulas',
    )
    ambiente = models.ForeignKey(
        Ambiente, verbose_name='Ambiente', on_delete=models.PROTECT, related_name='aulas',
    )
    dia_semana = models.CharField('Dia da semana', max_length=10, choices=DiaSemana.choices)
    horario = models.ForeignKey(
        Horario, verbose_name='Horário', on_delete=models.CASCADE, related_name='aulas',
    )
    ano_letivo = models.PositiveIntegerField('Ano letivo', default=ano_letivo_padrao)
    semestre = models.CharField(
        'Semestre', max_length=1, choices=Semestre.choices, default=Semestre.PRIMEIRO,
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Criado por', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='aulas_criadas',
    )
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Aula da grade'
        verbose_name_plural = 'Aulas da grade'
        ordering = ['ano_letivo', 'semestre', 'turma__nome', 'dia_semana', 'horario__ordem']
        constraints = [
            models.UniqueConstraint(
                fields=['turma', 'dia_semana', 'horario', 'ano_letivo', 'semestre'],
                name='grade_turma_sem_dupla_aula_no_mesmo_horario',
            ),
            models.UniqueConstraint(
                fields=['professor', 'dia_semana', 'horario', 'ano_letivo', 'semestre'],
                name='grade_professor_sem_duas_turmas_ao_mesmo_tempo',
            ),
        ]

    def __str__(self):
        return f'{self.turma} — {self.get_dia_semana_display()} {self.horario} — {self.disciplina.sigla}'

    def clean(self):
        erros = {}

        if self.ambiente_id and self.horario_id and self.dia_semana and self.ano_letivo and self.semestre:
            ocupacao = GradeAula.objects.filter(
                ambiente_id=self.ambiente_id, dia_semana=self.dia_semana, horario_id=self.horario_id,
                ano_letivo=self.ano_letivo, semestre=self.semestre,
            ).exclude(pk=self.pk).count()
            if ocupacao >= self.ambiente.capacidade:
                erros['ambiente'] = (
                    f'O ambiente "{self.ambiente}" já está com sua capacidade de uso simultâneo '
                    f'({self.ambiente.capacidade}) completa nesse dia e horário.'
                )

        if self.professor_id and self.horario_id and self.dia_semana:
            disponibilidade = DisponibilidadeProfessor.objects.filter(
                professor_id=self.professor_id, dia_semana=self.dia_semana, horario_id=self.horario_id,
            ).first()
            if disponibilidade is not None and not disponibilidade.disponivel:
                erros['professor'] = (
                    f'{self.professor.nome} marcou que não está disponível nesse dia e horário.'
                )

        if self.professor_id and self.ano_letivo and self.semestre:
            total_aulas = GradeAula.objects.filter(
                professor_id=self.professor_id, ano_letivo=self.ano_letivo, semestre=self.semestre,
            ).exclude(pk=self.pk).count()
            if total_aulas + 1 > self.professor.carga_horaria:
                mensagem = (
                    f'{self.professor.nome} tem carga horária semanal de {self.professor.carga_horaria} '
                    f'aula(s); esta seria a {total_aulas + 1}ª aula no {self.semestre}º semestre de '
                    f'{self.ano_letivo}.'
                )
                erros['professor'] = f'{erros.get("professor", "")} {mensagem}'.strip()

        if erros:
            raise ValidationError(erros)


class Atribuicao(models.Model):
    """
    Diz quem ensina o quê para qual turma — a base de dados que o
    algoritmo automático (Módulo 11, OR-Tools) usa para montar a grade
    sozinho. Sem isto, o solver não teria como saber, por exemplo, que o
    professor Carlos é quem dá Matemática para o 1º Ano A, nem quantas
    aulas semanais precisa encaixar (isso vem de
    `disciplina.quantidade_aulas_semana`).
    """
    turma = models.ForeignKey(
        Turma, verbose_name='Turma', on_delete=models.CASCADE, related_name='atribuicoes',
    )
    disciplina = models.ForeignKey(
        Disciplina, verbose_name='Disciplina', on_delete=models.CASCADE, related_name='atribuicoes',
    )
    professor = models.ForeignKey(
        Professor, verbose_name='Professor', on_delete=models.CASCADE, related_name='atribuicoes',
    )
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Atribuição de professor'
        verbose_name_plural = 'Atribuições de professores'
        ordering = ['turma__nome', 'disciplina__nome']
        constraints = [
            models.UniqueConstraint(
                fields=['turma', 'disciplina'], name='atribuicao_unica_por_turma_disciplina',
            ),
        ]

    def __str__(self):
        return f'{self.turma} — {self.disciplina.sigla} — {self.professor.nome}'
