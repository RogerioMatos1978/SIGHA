"""
View do Dashboard (Módulo 3). Uma única view simples: toda a complexidade
de agregação de dados fica em services.py.
"""
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from . import services


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        indicadores_usuarios = services.obter_indicadores_usuarios()
        contexto['indicadores_usuarios'] = indicadores_usuarios
        contexto['cartoes'] = services.obter_cartoes_resumo()
        contexto['grafico_papeis_labels'] = json.dumps(
            [item['papel'] for item in indicadores_usuarios['por_papel']]
        )
        contexto['grafico_papeis_valores'] = json.dumps(
            [item['quantidade'] for item in indicadores_usuarios['por_papel']]
        )
        return contexto
