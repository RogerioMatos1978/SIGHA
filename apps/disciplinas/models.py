"""
Modelo de Disciplina (Módulo 5).

quantidade_aulas_semana é o dado que o futuro motor de geração automática
(OR-Tools, Módulo 11) vai usar para saber quantas aulas de cada disciplina
precisam ser encaixadas na grade de cada turma por semana.
"""
from django.db import models

from apps.ambientes.models import TipoAmbiente


class Disciplina(models.Model):
    nome = models.CharField('Nome', max_length=100)
    sigla = models.CharField(
        'Sigla', max_length=10, unique=True,
        help_text='Código curto usado na grade (ex.: MAT, POR, HIST).',
    )
    quantidade_aulas_semana = models.PositiveSmallIntegerField(
        'Aulas por semana', default=1,
        help_text='Quantas aulas desta disciplina cada turma tem por semana.',
    )
    tipo_ambiente = models.CharField(
        'Tipo de ambiente necessário', max_length=20, choices=TipoAmbiente.choices,
        blank=True, null=True,
        help_text=(
            'Deixe em branco para usar uma sala comum. Preencha somente quando esta '
            'disciplina sempre precisar de um ambiente específico (ex.: Laboratório, '
            'Quadra) — o Módulo 11 (algoritmo automático) usa este dado para escolher '
            'o ambiente certo de cada aula.'
        ),
    )
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Disciplina'
        verbose_name_plural = 'Disciplinas'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.sigla})'
