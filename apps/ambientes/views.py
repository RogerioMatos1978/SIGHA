"""
Views do módulo Ambientes (Módulo 7). Mesmo padrão dos módulos anteriores.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, View

from .forms import AmbienteForm
from .models import Ambiente
from .permissions import GerenciaAcademicoMixin


class AmbienteListView(LoginRequiredMixin, GerenciaAcademicoMixin, ListView):
    model = Ambiente
    template_name = 'ambientes/ambiente_list.html'
    context_object_name = 'ambientes'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        termo = self.request.GET.get('q', '').strip()
        if termo:
            qs = qs.filter(Q(nome__icontains=termo) | Q(tipo__icontains=termo))
        return qs


class AmbienteCreateView(LoginRequiredMixin, GerenciaAcademicoMixin, SuccessMessageMixin, CreateView):
    model = Ambiente
    form_class = AmbienteForm
    template_name = 'ambientes/ambiente_form.html'
    success_url = reverse_lazy('ambientes:lista')
    success_message = 'Ambiente "%(nome)s" cadastrado com sucesso.'


class AmbienteUpdateView(LoginRequiredMixin, GerenciaAcademicoMixin, SuccessMessageMixin, UpdateView):
    model = Ambiente
    form_class = AmbienteForm
    template_name = 'ambientes/ambiente_form.html'
    success_url = reverse_lazy('ambientes:lista')
    success_message = 'Ambiente "%(nome)s" atualizado com sucesso.'


class AmbienteToggleAtivoView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    def post(self, request, pk):
        ambiente = get_object_or_404(Ambiente, pk=pk)
        ambiente.ativo = not ambiente.ativo
        ambiente.save(update_fields=['ativo'])
        estado = 'ativado' if ambiente.ativo else 'desativado'
        messages.success(request, f'Ambiente "{ambiente.nome}" {estado} com sucesso.')
        return redirect('ambientes:lista')
