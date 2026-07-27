"""
Views do módulo Professores (Módulo 4). Segue o mesmo padrão do módulo
Usuários: listar (com busca), criar, editar, ativar/desativar — nunca
excluir de verdade, para preservar o histórico.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, View

from .forms import ProfessorForm
from .models import Professor
from .permissions import GerenciaAcademicoMixin


class ProfessorListView(LoginRequiredMixin, GerenciaAcademicoMixin, ListView):
    model = Professor
    template_name = 'professores/professor_list.html'
    context_object_name = 'professores'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        termo = self.request.GET.get('q', '').strip()
        if termo:
            qs = qs.filter(Q(nome__icontains=termo) | Q(matricula__icontains=termo) | Q(email__icontains=termo))
        return qs


class ProfessorCreateView(LoginRequiredMixin, GerenciaAcademicoMixin, SuccessMessageMixin, CreateView):
    model = Professor
    form_class = ProfessorForm
    template_name = 'professores/professor_form.html'
    success_url = reverse_lazy('professores:lista')
    success_message = 'Professor "%(nome)s" cadastrado com sucesso.'


class ProfessorUpdateView(LoginRequiredMixin, GerenciaAcademicoMixin, SuccessMessageMixin, UpdateView):
    model = Professor
    form_class = ProfessorForm
    template_name = 'professores/professor_form.html'
    success_url = reverse_lazy('professores:lista')
    success_message = 'Professor "%(nome)s" atualizado com sucesso.'


class ProfessorToggleAtivoView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    def post(self, request, pk):
        professor = get_object_or_404(Professor, pk=pk)
        professor.ativo = not professor.ativo
        professor.save(update_fields=['ativo'])
        estado = 'ativado' if professor.ativo else 'desativado'
        messages.success(request, f'Professor "{professor.nome}" {estado} com sucesso.')
        return redirect('professores:lista')
