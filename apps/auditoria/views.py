"""
View do módulo Auditoria (Módulo 16): consulta paginada dos registros,
com filtros por modelo, ação e usuário.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import Acao, RegistroAuditoria
from .permissions import SomenteAdministradorMixin


class RegistroAuditoriaListView(LoginRequiredMixin, SomenteAdministradorMixin, ListView):
    model = RegistroAuditoria
    template_name = 'auditoria/lista.html'
    context_object_name = 'registros'
    paginate_by = 50

    def get_queryset(self):
        qs = RegistroAuditoria.objects.select_related('usuario').all()
        params = self.request.GET
        modelo = params.get('modelo')
        acao = params.get('acao')
        usuario_id = params.get('usuario')
        if modelo:
            qs = qs.filter(modelo=modelo)
        if acao:
            qs = qs.filter(acao=acao)
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
        return qs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['acoes'] = Acao.choices
        contexto['modelos'] = (
            RegistroAuditoria.objects.exclude(modelo='').order_by('modelo')
            .values_list('modelo', flat=True).distinct()
        )
        return contexto
