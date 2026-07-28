"""
Views do módulo Disponibilidade (Módulo 9).

Em vez de um CRUD tradicional (um registro por vez), a edição acontece
numa grade única por professor — dias nas colunas, horários nas linhas —
igual ao pedido na especificação para a visualização da Grade.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views.generic import ListView, View

from apps.professores.models import Professor

from . import services
from .models import DiaSemana
from .permissions import GerenciaAcademicoMixin


class ProfessorDisponibilidadeListView(LoginRequiredMixin, GerenciaAcademicoMixin, ListView):
    """Lista professores ativos para escolher de quem editar a disponibilidade."""
    model = Professor
    template_name = 'disponibilidade/professor_lista.html'
    context_object_name = 'professores'
    paginate_by = 20

    def get_queryset(self):
        qs = Professor.objects.filter(ativo=True)
        termo = self.request.GET.get('q', '').strip()
        if termo:
            qs = qs.filter(Q(nome__icontains=termo) | Q(matricula__icontains=termo))
        return qs.order_by('nome')


class DisponibilidadeGradeView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    """GET mostra a grade do professor; POST salva as alterações."""
    template_name = 'disponibilidade/grade.html'

    def get(self, request, professor_id):
        professor = get_object_or_404(Professor, pk=professor_id)
        grade = services.montar_grade(professor)
        return render(request, self.template_name, {
            'professor': professor,
            'grade': grade,
            'dias': DiaSemana.choices,
        })

    def post(self, request, professor_id):
        professor = get_object_or_404(Professor, pk=professor_id)
        services.salvar_grade(professor, request.POST)
        messages.success(request, f'Disponibilidade de {professor.nome} atualizada com sucesso.')
        return redirect(reverse('disponibilidade:editar', args=[professor.pk]))
