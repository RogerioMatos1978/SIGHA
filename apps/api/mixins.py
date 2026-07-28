"""
Mixin de validação da API (Módulo 15): reaproveita `Model.full_clean()`
em vez de duplicar, na Serializer, regras de negócio que já existem no
modelo (Módulos 8, 10 e 12 — horário, grade e calendário).
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


class FullCleanMixin:
    """
    Depois que os campos passam pela validação padrão do DRF, monta uma
    instância do modelo com esses dados (sem salvar) e chama
    `full_clean()`. Qualquer `ValidationError` do Django vira erro de
    campo da API, com a mesma mensagem mostrada nas telas web.
    """
    excluir_do_full_clean = []

    def validate(self, dados):
        modelo = self.Meta.model
        if self.instance is not None:
            instancia = self.instance
            for campo, valor in dados.items():
                setattr(instancia, campo, valor)
        else:
            instancia = modelo(**dados)
        self.preparar_instancia(instancia)
        try:
            instancia.full_clean(exclude=self.excluir_do_full_clean)
        except DjangoValidationError as erro:
            detalhe = erro.message_dict if hasattr(erro, 'message_dict') else {'non_field_errors': erro.messages}
            raise serializers.ValidationError(detalhe)
        return dados

    def preparar_instancia(self, instancia):
        """Hook para preencher campos que a Serializer não recebe do cliente (ex.: criado_por)."""
