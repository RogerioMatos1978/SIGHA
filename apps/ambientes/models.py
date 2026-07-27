"""
Modelo de Ambiente (Módulo 7).

Biblioteca, laboratórios e quadra são todos "Ambiente" com tipos
diferentes — não modelos separados — porque a regra de negócio central
(nunca dois horários conflitantes no mesmo ambiente quando a capacidade
para uso simultâneo é 1) é idêntica para todos e será aplicada de forma
genérica no módulo de Grade (Módulo 8), a partir do campo `capacidade`.
"""
from django.db import models


class TipoAmbiente(models.TextChoices):
    SALA = 'SALA', 'Sala'
    BIBLIOTECA = 'BIBLIOTECA', 'Biblioteca'
    LABORATORIO = 'LABORATORIO', 'Laboratório'
    QUADRA = 'QUADRA', 'Quadra'
    AUDITORIO = 'AUDITORIO', 'Auditório'
    MAKER = 'MAKER', 'Maker'


class Ambiente(models.Model):
    nome = models.CharField('Nome', max_length=100, help_text='Ex.: Laboratório de Informática, Quadra Poliesportiva.')
    tipo = models.CharField('Tipo', max_length=20, choices=TipoAmbiente.choices)
    capacidade = models.PositiveSmallIntegerField(
        'Capacidade de uso simultâneo', default=1,
        help_text='Quantas turmas podem usar este ambiente ao mesmo tempo (normalmente 1).',
    )
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Ambiente'
        verbose_name_plural = 'Ambientes'
        ordering = ['tipo', 'nome']
        constraints = [
            models.UniqueConstraint(fields=['nome'], name='ambiente_nome_unico'),
        ]

    def __str__(self):
        return f'{self.nome} ({self.get_tipo_display()})'
