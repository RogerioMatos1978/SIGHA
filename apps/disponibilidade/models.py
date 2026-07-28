"""
Modelo de Disponibilidade de Professor (Módulo 9).

Cruza Professor x Dia da semana x Horário, com um booleano "disponível".
O futuro motor de geração automática (OR-Tools, Módulo 11) vai ler esta
tabela para nunca escalar um professor num horário em que ele marcou que
não pode dar aula.
"""
from django.db import models

from apps.horarios.models import Horario
from apps.professores.models import Professor


class DiaSemana(models.TextChoices):
    """Dias letivos considerados pela grade (segunda a sexta)."""
    SEGUNDA = 'SEGUNDA', 'Segunda-feira'
    TERCA = 'TERCA', 'Terça-feira'
    QUARTA = 'QUARTA', 'Quarta-feira'
    QUINTA = 'QUINTA', 'Quinta-feira'
    SEXTA = 'SEXTA', 'Sexta-feira'


class DisponibilidadeProfessor(models.Model):
    professor = models.ForeignKey(
        Professor, verbose_name='Professor', on_delete=models.CASCADE,
        related_name='disponibilidades',
    )
    dia_semana = models.CharField('Dia da semana', max_length=10, choices=DiaSemana.choices)
    horario = models.ForeignKey(
        Horario, verbose_name='Horário', on_delete=models.CASCADE,
        related_name='disponibilidades',
    )
    disponivel = models.BooleanField('Disponível', default=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Disponibilidade de professor'
        verbose_name_plural = 'Disponibilidades de professores'
        ordering = ['professor__nome', 'dia_semana', 'horario__ordem']
        constraints = [
            models.UniqueConstraint(
                fields=['professor', 'dia_semana', 'horario'],
                name='disponibilidade_unica_por_professor_dia_horario',
            ),
        ]

    def __str__(self):
        situacao = 'disponível' if self.disponivel else 'indisponível'
        return f'{self.professor.nome} — {self.get_dia_semana_display()} {self.horario} ({situacao})'
