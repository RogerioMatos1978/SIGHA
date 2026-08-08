"""
Views do módulo Turmas (Módulo 6). Mesmo padrão dos módulos anteriores.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, View

from .forms import TurmaForm
from .models import EtapaEnsino, Turma
from .permissions import GerenciaAcademicoMixin


class TurmaListView(LoginRequiredMixin, GerenciaAcademicoMixin, ListView):
    model = Turma
    template_name = 'turmas/turma_list.html'
    context_object_name = 'turmas'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        termo = self.request.GET.get('q', '').strip()
        if termo:
            qs = qs.filter(Q(nome__icontains=termo) | Q(serie__icontains=termo))
        etapa = self.request.GET.get('etapa_ensino')
        if etapa:
            qs = qs.filter(etapa_ensino=etapa)
        return qs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['etapas'] = EtapaEnsino.choices
        return contexto


class TurmaCreateView(LoginRequiredMixin, GerenciaAcademicoMixin, SuccessMessageMixin, CreateView):
    model = Turma
    form_class = TurmaForm
    template_name = 'turmas/turma_form.html'
    success_url = reverse_lazy('turmas:lista')
    success_message = 'Turma "%(nome)s" cadastrada com sucesso.'


class TurmaUpdateView(LoginRequiredMixin, GerenciaAcademicoMixin, SuccessMessageMixin, UpdateView):
    model = Turma
    form_class = TurmaForm
    template_name = 'turmas/turma_form.html'
    success_url = reverse_lazy('turmas:lista')
    success_message = 'Turma "%(nome)s" atualizada com sucesso.'


class TurmaToggleAtivoView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    def post(self, request, pk):
        turma = get_object_or_404(Turma, pk=pk)
        turma.ativo = not turma.ativo
        turma.save(update_fields=['ativo'])
        estado = 'ativada' if turma.ativo else 'desativada'
        messages.success(request, f'Turma "{turma.nome}" {estado} com sucesso.')
        return redirect('turmas:lista')
