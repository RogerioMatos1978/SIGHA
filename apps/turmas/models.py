"""
Modelo de Turma (Módulo 6).

O Turno mora aqui (e não em "horarios") porque é um atributo da própria
turma — toda turma tem um turno fixo — e os módulos futuros (Horários,
Grade) vão filtrar/relacionar horários a partir do turno da turma.

A Etapa de Ensino segue a divisão oficial do MEC/LDB (Lei de Diretrizes
e Bases): Ensino Fundamental I — "Anos Iniciais" — do 1º ao 5º ano;
Ensino Fundamental II — "Anos Finais" — do 6º ao 9º ano; Ensino Médio,
com 3 anos (1º ao 3º); e Curso Técnico (Módulo 20), para as turmas dos
cursos técnicos ofertados junto com o SENAI. É um campo próprio (não
deduzido do texto livre de `serie`) porque `serie` aceita qualquer
nomenclatura que a escola já usa (ex.: "3ª Série" em vez de "9º Ano"),
então a única forma confiável de agrupar/filtrar por etapa é a
coordenação escolher explicitamente.

Cursos Técnicos (Módulo 20): a lista de `CursoTecnico` reproduz o
catálogo nacional de cursos técnicos do SENAI (eixo/área/segmento
tecnológico e carga horária conforme divulgado pelo SENAI Goiás e pela
SEDUC-GO, https://conteudo.senaigoias.com.br/cursos-tecnicos e
https://goias.gov.br/educacao/lista-de-cursos-etp-com-o-senai/) — é uma
lista fixa (TextChoices), como Turno e EtapaEnsino, porque o SENAI define
esse catálogo nacionalmente; não é algo que a escola cadastra do zero.
`codigo_evento` é o código interno que o SENAI atribui a cada TURMA
(cada "evento"/oferta específica de um curso, com data e vagas próprias)
dentro do sistema deles (SGE) — por isso mora na Turma, não no curso.
"""
from django.core.exceptions import ValidationError
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
    TECNICO = 'TECNICO', 'Curso Técnico (SENAI)'


class CursoTecnico(models.TextChoices):
    """Catálogo nacional de cursos técnicos do SENAI (eixo Controle e Processos Industriais e afins)."""
    ALIMENTOS = 'ALIMENTOS', 'Técnico em Alimentos'
    AUTOMACAO_INDUSTRIAL = 'AUTOMACAO_INDUSTRIAL', 'Técnico em Automação Industrial'
    DESENVOLVIMENTO_DE_SISTEMAS = 'DESENVOLVIMENTO_DE_SISTEMAS', 'Técnico em Desenvolvimento de Sistemas'
    DESIGN_GRAFICO = 'DESIGN_GRAFICO', 'Técnico em Design Gráfico'
    EDIFICACOES = 'EDIFICACOES', 'Técnico em Edificações'
    ELETROMECANICA = 'ELETROMECANICA', 'Técnico em Eletromecânica'
    ELETROTECNICA = 'ELETROTECNICA', 'Técnico em Eletrotécnica'
    MANUTENCAO_AUTOMOTIVA = 'MANUTENCAO_AUTOMOTIVA', 'Técnico em Manutenção Automotiva'
    MANUTENCAO_DE_MAQUINAS_INDUSTRIAIS = 'MANUTENCAO_DE_MAQUINAS_INDUSTRIAIS', 'Técnico em Manutenção de Máquinas Industriais'
    MANUTENCAO_E_SUPORTE_EM_INFORMATICA = 'MANUTENCAO_E_SUPORTE_EM_INFORMATICA', 'Técnico em Manutenção e Suporte em Informática'
    MECANICA = 'MECANICA', 'Técnico em Mecânica'
    MECATRONICA = 'MECATRONICA', 'Técnico em Mecatrônica'
    PROGRAMACAO_DE_JOGOS_DIGITAIS = 'PROGRAMACAO_DE_JOGOS_DIGITAIS', 'Técnico em Programação de Jogos Digitais'
    QUIMICA = 'QUIMICA', 'Técnico em Química'
    REDES_DE_COMPUTADORES = 'REDES_DE_COMPUTADORES', 'Técnico em Redes de Computadores'
    VESTUARIO = 'VESTUARIO', 'Técnico em Vestuário'


class Turma(models.Model):
    nome = models.CharField('Nome', max_length=50, help_text='Ex.: 1º Ano A, 9º Ano B.')
    serie = models.CharField('Série', max_length=50, help_text='Ex.: 1º Ano, 9º Ano, 3ª Série.')
    etapa_ensino = models.CharField(
        'Etapa de ensino', max_length=20, choices=EtapaEnsino.choices,
        default=EtapaEnsino.FUNDAMENTAL_2,
        help_text='Fundamental I, Fundamental II, Médio ou Curso Técnico, conforme a divisão do MEC/LDB.',
    )
    curso_tecnico = models.CharField(
        'Curso técnico', max_length=40, choices=CursoTecnico.choices, blank=True,
        help_text='Preencha somente quando a etapa de ensino for "Curso Técnico".',
    )
    codigo_evento = models.CharField(
        'Código do evento', max_length=30, blank=True,
        help_text='Código interno que o SENAI atribui a esta turma/oferta específica do curso (sistema SGE).',
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
        if self.etapa_ensino == EtapaEnsino.TECNICO and self.curso_tecnico:
            return f'{self.nome} — {self.get_curso_tecnico_display()} ({self.get_turno_display()})'
        return f'{self.nome} ({self.get_turno_display()})'

    def clean(self):
        if self.etapa_ensino == EtapaEnsino.TECNICO and not self.curso_tecnico:
            raise ValidationError({
                'curso_tecnico': 'Informe qual curso técnico esta turma é, já que a etapa de ensino é "Curso Técnico".',
            })
