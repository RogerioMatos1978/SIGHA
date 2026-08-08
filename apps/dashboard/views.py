"""
View do Dashboard (Módulo 3). Uma única view simples: toda a complexidade
de agregação de dados fica em services.py.

Módulo 20: o dashboard trocou o gráfico "Usuários por papel" por um
painel de planejamento do dia (aulas e eventos de hoje) — mais amigável
e mais útil no dia a dia do que um gráfico decorativo.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from . import services


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['indicadores_usuarios'] = services.obter_indicadores_usuarios()
        contexto['cartoes'] = services.obter_cartoes_resumo()
        contexto['planejamento_hoje'] = services.obter_planejamento_do_dia()
        return contexto
