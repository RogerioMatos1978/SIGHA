"""
Modelo de Turma (Módulo 6).

O Turno mora aqui (e não em "horarios") porque é um atributo da própria
turma — toda turma tem um turno fixo — e os módulos futuros (Horários,
Grade) vão filtrar/relacionar horários a partir do turno da turma.
"""
from django.db import models


class Turno(models.TextChoices):
    MATUTINO = 'MATUTINO', 'Matutino'
    VESPERTINO = 'VESPERTINO', 'Vespertino'
    NOTURNO = 'NOTURNO', 'Noturno'
    INTEGRAL = 'INTEGRAL', 'Integral'


class Turma(models.Model):
    nome = models.CharField('Nome', max_length=50, help_text='Ex.: 1º Ano A, 9º Ano B.')
    serie = models.CharField('Série', max_length=50, help_text='Ex.: 1º Ano, 9º Ano, 3ª Série.')
    turno = models.CharField('Turno', max_length=20, choices=Turno.choices)
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Turma'
        verbose_name_plural = 'Turmas'
        ordering = ['serie', 'nome']
        constraints = [
            models.UniqueConstraint(fields=['nome', 'turno'], name='turma_nome_turno_unico'),
        ]

    def __str__(self):
        return f'{self.nome} ({self.get_turno_display()})'
