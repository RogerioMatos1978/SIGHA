"""
Permissões da API (Módulo 15) — espelham, para o DRF, as mesmas regras já
aplicadas nas telas web (`apps.usuarios.permissions`), em vez de criar um
segundo sistema de papéis paralelo.
"""
from rest_framework.permissions import BasePermission


class PermiteGerenciarAcademico(BasePermission):
    message = 'Você não tem permissão para gerenciar dados acadêmicos.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.pode_gerenciar_academico())


class PermiteGerenciarUsuarios(BasePermission):
    message = 'Você não tem permissão para gerenciar usuários.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.pode_gerenciar_usuarios())
