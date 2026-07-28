"""
Modelo de Evento do Calendário Acadêmico (Módulo 12).

Guarda feriados, recessos, provas e outros eventos que marcam o
calendário letivo do ano. `afeta_aulas=True` significa "neste período não
há aula normal" (feriado/recesso) — é essa informação que a tela de
detalhe do dia usa para avisar que não há aula, sem precisar mexer na
Grade recorrente por dia da semana (Módulo 10), que continua sendo o
"modelo" semanal de aulas independente do calendário de datas.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def ano_letivo_padrao():
    return timezone.now().year


class TipoEvento(models.TextChoices):
    FERIADO = 'FERIADO', 'Feriado'
    RECESSO = 'RECESSO', 'Recesso escolar'
    PROVA = 'PROVA', 'Prova/Avaliação'
    EVENTO = 'EVENTO', 'Evento escolar'
    REUNIAO = 'REUNIAO', 'Reunião pedagógica'
    OUTRO = 'OUTRO', 'Outro'


class Evento(models.Model):
    titulo = models.CharField('Título', max_length=150)
    tipo = models.CharField('Tipo', max_length=20, choices=TipoEvento.choices, default=TipoEvento.EVENTO)
    data_inicio = models.DateField('Data de início')
    data_fim = models.DateField(
        'Data de fim', blank=True, null=True,
        help_text='Deixe em branco se o evento dura só um dia.',
    )
    descricao = models.TextField('Descrição', blank=True)
    afeta_aulas = models.BooleanField(
        'Não há aula normal neste período', default=False,
        help_text='Marque para feriados e recessos — avisa quem consultar o calendário que não há aula.',
    )
    ano_letivo = models.PositiveIntegerField('Ano letivo', default=ano_letivo_padrao)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Criado por', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='eventos_criados',
    )
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Evento do calendário'
        verbose_name_plural = 'Eventos do calendário'
        ordering = ['data_inicio', 'titulo']

    def __str__(self):
        return f'{self.titulo} ({self.data_inicio})'

    def clean(self):
        if self.data_fim and self.data_inicio and self.data_fim < self.data_inicio:
            raise ValidationError({'data_fim': 'A data de fim não pode ser antes da data de início.'})

    @property
    def fim_efetivo(self):
        return self.data_fim or self.data_inicio
