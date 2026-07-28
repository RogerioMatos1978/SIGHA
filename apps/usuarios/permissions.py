"""
Regras de autorização compartilhadas entre os módulos, centralizadas aqui
(Responsabilidade Única do SOLID) em vez de espalhadas pelas views.
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class _NegaPorPapelMixin(UserPassesTestMixin):
    """
    Comportamento comum das checagens de papel: quem NÃO está logado é
    redirecionado para o login (302); quem está logado mas não tem o
    papel exigido recebe "acesso negado" (403). Sem isso, o Django trata
    os dois casos da mesma forma e um visitante anônimo cai numa tela de
    403 em vez de ir para o login.
    """
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied(self.get_permission_denied_message())
        return super().handle_no_permission()


class GerenciaUsuariosMixin(_NegaPorPapelMixin):
    """
    Mixin de CBV: só deixa passar Administrador ou Coordenador.
    Qualquer view de criação/edição/exclusão de usuário deve usar isto.
    """
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.pode_gerenciar_usuarios()


class GerenciaAcademicoMixin(_NegaPorPapelMixin):
    """
    Mixin de CBV reutilizado pelos módulos de cadastro acadêmico
    (Professores, Disciplinas, Turmas, Ambientes...): só deixa passar
    Administrador, Coordenador e Secretaria.
    """
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.pode_gerenciar_academico()


class SomenteAdministradorMixin(_NegaPorPapelMixin):
    """
    Mixin de CBV para telas mais sensíveis que o cadastro acadêmico comum
    — hoje, só a consulta de Auditoria (Módulo 16), que expõe quem mexeu
    em quê no sistema inteiro, inclusive em registros de outros usuários.
    """
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.is_administrador()
