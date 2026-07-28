"""
Modelo de Horário (Módulo 8).

Representa uma "linha" da grade — ex.: 07:00–07:50 é a 1ª aula do dia.
Nada aqui é fixo: a instituição cadastra a quantidade de horários que
quiser, na ordem que quiser, incluindo intervalos. Os módulos futuros
(Disponibilidade, Grade) sempre vão referenciar este modelo em vez de
hardcodar horários no código — exatamente a regra "horários configuráveis"
da especificação.
"""
from django.core.exceptions import ValidationError
from django.db import models


class Horario(models.Model):
    ordem = models.PositiveSmallIntegerField(
        'Ordem', unique=True,
        help_text='Posição deste horário na grade do dia (1, 2, 3...).',
    )
    inicio = models.TimeField('Início')
    fim = models.TimeField('Fim')
    intervalo = models.BooleanField(
        'É intervalo/recreio', default=False,
        help_text='Marque se este período é um intervalo, não uma aula.',
    )
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Horário'
        verbose_name_plural = 'Horários'
        ordering = ['ordem']

    def __str__(self):
        rotulo = 'Intervalo' if self.intervalo else f'{self.ordem}ª aula'
        return f'{rotulo} ({self.inicio.strftime("%H:%M")}–{self.fim.strftime("%H:%M")})'

    def clean(self):
        if self.inicio and self.fim and self.fim <= self.inicio:
            raise ValidationError({'fim': 'O horário de término deve ser depois do início.'})
