"""
Views do módulo Substituições (Módulo 19).

Uma Substituição sempre nasce a partir de uma aula específica da Grade
(o botão "Substituir" na grade visual, Módulo 10) — por isso o Create
recebe `aula_id` pela URL, igual ao padrão já usado em GradeAulaCreateView.
A lista é geral (todas as substituições da escola, mais recentes primeiro),
com filtro opcional por turma, para o coordenador acompanhar quem cobriu o quê.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DeleteView, ListView

from apps.grade.models import GradeAula
from apps.turmas.models import Turma

from .forms import SubstituicaoForm
from .models import Substituicao
from .permissions import GerenciaAcademicoMixin


class SubstituicaoListView(LoginRequiredMixin, GerenciaAcademicoMixin, ListView):
    """Lista geral de substituições já registradas — mais recentes primeiro."""
    model = Substituicao
    template_name = 'substituicoes/substituicao_lista.html'
    context_object_name = 'substituicoes'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'aula__turma', 'aula__disciplina', 'aula__professor', 'professor_substituto',
        )
        turma_id = self.request.GET.get('turma')
        if turma_id:
            qs = qs.filter(aula__turma_id=turma_id)
        return qs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['turmas'] = Turma.objects.filter(ativo=True).order_by('serie', 'nome')
        contexto['turma_selecionada'] = self.request.GET.get('turma', '')
        return contexto


class SubstituicaoCreateView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    """Registra que, numa data específica, outro professor assumiu (ou a aula foi cancelada)."""
    template_name = 'substituicoes/substituicao_form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.aula = get_object_or_404(GradeAula, pk=kwargs['aula_id'])

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': SubstituicaoForm(), 'aula': self.aula})

    def post(self, request, *args, **kwargs):
        form = SubstituicaoForm(request.POST)
        if form.is_valid():
            substituicao = form.save(commit=False)
            substituicao.aula = self.aula
            substituicao.criado_por = request.user
            try:
                substituicao.full_clean()
            except ValidationError as erro:
                form.add_error(None, erro)
                return render(request, self.template_name, {'form': form, 'aula': self.aula})
            substituicao.save()
            if substituicao.professor_substituto and not substituicao.professor_substituto.pode_lecionar_em(self.aula.turma):
                messages.warning(
                    request,
                    f'Substituição registrada. Atenção: {substituicao.professor_substituto.nome} não está '
                    f'vinculado à etapa/turma de "{self.aula.turma.nome}" — confira se é mesmo quem deve cobrir esta aula.',
                )
            else:
                messages.success(request, 'Substituição registrada com sucesso.')
            return redirect(
                f"{reverse('grade:visual', args=[self.aula.turma_id])}"
                f"?ano={self.aula.ano_letivo}&semestre={self.aula.semestre}"
            )
        return render(request, self.template_name, {'form': form, 'aula': self.aula})


class SubstituicaoDeleteView(LoginRequiredMixin, GerenciaAcademicoMixin, DeleteView):
    """Cancela/remove um registro de substituição (ex.: lançado por engano)."""
    model = Substituicao
    template_name = 'substituicoes/substituicao_confirmar_remocao.html'
    context_object_name = 'substituicao'

    def get_success_url(self):
        messages.success(self.request, 'Substituição removida.')
        return reverse('substituicoes:lista')
