"""
Regras de autorização do módulo Usuários, centralizadas aqui (princípio
da Responsabilidade Única do SOLID) em vez de espalhadas pelas views.
"""
from django.contrib.auth.mixins import UserPassesTestMixin


class GerenciaUsuariosMixin(UserPassesTestMixin):
    """
    Mixin de CBV: só deixa passar Administrador ou Coordenador.
    Qualquer view de criação/edição/exclusão de usuário deve usar isto.
    """
    raise_exception = True  # devolve 403 em vez de redirecionar silenciosamente

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.pode_gerenciar_usuarios()
