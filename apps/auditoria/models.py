"""
Modelo de Auditoria (Módulo 16).

Registra quem criou, alterou ou removeu cada registro dos modelos
acadêmicos — pela tela web, pelo admin do Django ou pela API (Módulo
15) — sempre pelo mesmo caminho: sinais `post_save`/`post_delete`
conectados em `signals.py`, mais os sinais de login/logout do Django.

Não guarda o "antes e depois" campo a campo (ficaria pesado sem trazer
muito benefício prático para o volume de dados de uma escola); guarda o
retrato do objeto (`objeto_repr`) no momento da ação — suficiente para
responder "quem fez o quê e quando".
"""
from django.conf import settings
from django.db import models


class Acao(models.TextChoices):
    CRIACAO = 'CRIACAO', 'Criação'
    ATUALIZACAO = 'ATUALIZACAO', 'Atualização'
    REMOCAO = 'REMOCAO', 'Remoção'
    LOGIN = 'LOGIN', 'Login'
    LOGIN_FALHOU = 'LOGIN_FALHOU', 'Tentativa de login falhou'
    LOGOUT = 'LOGOUT', 'Logout'


class RegistroAuditoria(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Usuário', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='registros_auditoria',
        help_text='Em branco quando a ação foi de um visitante não autenticado (ex.: login que falhou).',
    )
    acao = models.CharField('Ação', max_length=20, choices=Acao.choices)
    modelo = models.CharField('Modelo', max_length=100, blank=True)
    objeto_id = models.CharField('ID do objeto', max_length=50, blank=True)
    objeto_repr = models.CharField('Descrição do objeto', max_length=300, blank=True)
    ip = models.GenericIPAddressField('Endereço IP', null=True, blank=True)
    criado_em = models.DateTimeField('Data/hora', auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de auditoria'
        verbose_name_plural = 'Registros de auditoria'
        ordering = ['-criado_em']

    def __str__(self):
        quem = self.usuario.username if self.usuario else 'visitante'
        alvo = f'{self.modelo} #{self.objeto_id}'.strip() if self.modelo else ''
        return f'{self.criado_em:%d/%m/%Y %H:%M} — {quem} — {self.get_acao_display()} {alvo}'.strip()
