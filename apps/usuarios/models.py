"""
Modelo de usuário do SIGHA (Módulo 1).

Usamos um modelo customizado (em vez do User padrão do Django) porque
o sistema precisa de campos próprios — matrícula, telefone, papel — e
porque trocar o modelo de usuário depois de o projeto crescer é muito
mais trabalhoso do que defini-lo corretamente desde o início.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class Papel(models.TextChoices):
    """
    Perfis de acesso previstos na especificação do sistema.
    Cada papel será usado pelas views/permissions dos próximos módulos
    para liberar ou bloquear ações (ex.: só Administrador exclui usuários).
    """
    ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'
    COORDENADOR = 'COORDENADOR', 'Coordenador'
    SECRETARIA = 'SECRETARIA', 'Secretaria'
    PROFESSOR = 'PROFESSOR', 'Professor'
    CONSULTA = 'CONSULTA', 'Consulta'


class Usuario(AbstractUser):
    """
    Usuário do sistema. Estende o AbstractUser do Django (que já traz
    username, password com hash, e-mail, last_login etc.) e adiciona os
    campos exigidos pela especificação do SIGHA.
    """
    matricula = models.CharField(
        'Matrícula', max_length=20, unique=True, blank=True, null=True,
        help_text='Matrícula institucional (obrigatória para professores).',
    )
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    papel = models.CharField(
        'Papel', max_length=20, choices=Papel.choices, default=Papel.CONSULTA,
    )
    ativo = models.BooleanField(
        'Ativo', default=True,
        help_text='Usuários inativos não conseguem fazer login, mas seu '
                   'histórico é preservado (nunca excluímos um cadastro).',
    )
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        nome = self.get_full_name() or self.username
        return f'{nome} ({self.get_papel_display()})'

    @property
    def esta_liberado_para_login(self):
        """Regra de negócio central: usuário inativo nunca acessa o sistema."""
        return self.is_active and self.ativo

    def is_administrador(self):
        return self.papel == Papel.ADMINISTRADOR or self.is_superuser

    def is_coordenador(self):
        return self.papel == Papel.COORDENADOR

    def pode_gerenciar_usuarios(self):
        """Somente Administrador e Coordenador cadastram/editam usuários."""
        return self.is_administrador() or self.is_coordenador()
