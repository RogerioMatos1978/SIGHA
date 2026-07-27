"""
Views do módulo Disciplinas (Módulo 5). Mesmo padrão de Professores e
Usuários: listar (com busca), criar, editar, ativar/desativar.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, View

from .forms import DisciplinaForm
from .models import Disciplina
from .permissions import GerenciaAcademicoMixin


class DisciplinaListView(LoginRequiredMixin, GerenciaAcademicoMixin, ListView):
    model = Disciplina
    template_name = 'disciplinas/disciplina_list.html'
    context_object_name = 'disciplinas'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        termo = self.request.GET.get('q', '').strip()
        if termo:
            qs = qs.filter(Q(nome__icontains=termo) | Q(sigla__icontains=termo))
        return qs


class DisciplinaCreateView(LoginRequiredMixin, GerenciaAcademicoMixin, SuccessMessageMixin, CreateView):
    model = Disciplina
    form_class = DisciplinaForm
    template_name = 'disciplinas/disciplina_form.html'
    success_url = reverse_lazy('disciplinas:lista')
    success_message = 'Disciplina "%(nome)s" cadastrada com sucesso.'


class DisciplinaUpdateView(LoginRequiredMixin, GerenciaAcademicoMixin, SuccessMessageMixin, UpdateView):
    model = Disciplina
    form_class = DisciplinaForm
    template_name = 'disciplinas/disciplina_form.html'
    success_url = reverse_lazy('disciplinas:lista')
    success_message = 'Disciplina "%(nome)s" atualizada com sucesso.'


class DisciplinaToggleAtivoView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    def post(self, request, pk):
        disciplina = get_object_or_404(Disciplina, pk=pk)
        disciplina.ativo = not disciplina.ativo
        disciplina.save(update_fields=['ativo'])
        estado = 'ativada' if disciplina.ativo else 'desativada'
        messages.success(request, f'Disciplina "{disciplina.nome}" {estado} com sucesso.')
        return redirect('disciplinas:lista')
