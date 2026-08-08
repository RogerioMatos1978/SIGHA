"""
Modelo de Turma (Módulo 6).

O Turno mora aqui (e não em "horarios") porque é um atributo da própria
turma — toda turma tem um turno fixo — e os módulos futuros (Horários,
Grade) vão filtrar/relacionar horários a partir do turno da turma.

A Etapa de Ensino segue a divisão oficial do MEC/LDB (Lei de Diretrizes
e Bases): Ensino Fundamental I — "Anos Iniciais" — do 1º ao 5º ano;
Ensino Fundamental II — "Anos Finais" — do 6º ao 9º ano; e Ensino Médio,
com 3 anos (1º ao 3º). É um campo próprio (não deduzido do texto livre
de `serie`) porque `serie` aceita qualquer nomenclatura que a escola já
usa (ex.: "3ª Série" em vez de "9º Ano"), então a única forma confiável
de agrupar/filtrar por etapa é a coordenação escolher explicitamente.
"""
from django.db import models


class Turno(models.TextChoices):
    MATUTINO = 'MATUTINO', 'Matutino'
    VESPERTINO = 'VESPERTINO', 'Vespertino'
    NOTURNO = 'NOTURNO', 'Noturno'
    INTEGRAL = 'INTEGRAL', 'Integral'


class EtapaEnsino(models.TextChoices):
    FUNDAMENTAL_1 = 'FUNDAMENTAL_1', 'Ensino Fundamental I (Anos Iniciais — 1º ao 5º ano)'
    FUNDAMENTAL_2 = 'FUNDAMENTAL_2', 'Ensino Fundamental II (Anos Finais — 6º ao 9º ano)'
    MEDIO = 'MEDIO', 'Ensino Médio (1º ao 3º ano)'


class Turma(models.Model):
    nome = models.CharField('Nome', max_length=50, help_text='Ex.: 1º Ano A, 9º Ano B.')
    serie = models.CharField('Série', max_length=50, help_text='Ex.: 1º Ano, 9º Ano, 3ª Série.')
    etapa_ensino = models.CharField(
        'Etapa de ensino', max_length=20, choices=EtapaEnsino.choices,
        default=EtapaEnsino.FUNDAMENTAL_2,
        help_text='Fundamental I, Fundamental II ou Médio, conforme a divisão do MEC/LDB.',
    )
    turno = models.CharField('Turno', max_length=20, choices=Turno.choices)
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Turma'
        verbose_name_plural = 'Turmas'
        ordering = ['etapa_ensino', 'serie', 'nome']
        constraints = [
            models.UniqueConstraint(fields=['nome', 'turno'], name='turma_nome_turno_unico'),
        ]

    def __str__(self):
        return f'{self.nome} ({self.get_turno_display()})'
