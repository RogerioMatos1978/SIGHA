"""
Modelo de Professor (Módulo 4).

É uma entidade própria — separada do Usuário de login — porque nem todo
professor necessariamente acessa o sistema, e porque os módulos futuros
(Disponibilidade, Grade) precisam referenciar "o professor" independente
de ele ter ou não uma conta. Quando o professor também precisa fazer
login (para ver a própria grade, por exemplo), ele é vinculado a um
Usuário com papel=PROFESSOR através do campo `usuario`.
"""
from django.conf import settings
from django.db import models


class Professor(models.Model):
    nome = models.CharField('Nome completo', max_length=150)
    matricula = models.CharField('Matrícula', max_length=20, unique=True)
    email = models.EmailField('E-mail', blank=True)
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    carga_horaria = models.PositiveSmallIntegerField(
        'Carga horária semanal (aulas)', default=0,
        help_text='Quantidade máxima de aulas semanais deste professor.',
    )
    ativo = models.BooleanField('Ativo', default=True)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name='Usuário de login (opcional)',
        on_delete=models.SET_NULL, null=True, blank=True, related_name='professor',
        help_text='Preencha somente se este professor também tiver acesso ao sistema.',
    )
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Professor'
        verbose_name_plural = 'Professores'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.matricula})'
