"""
Views do módulo Grade (Módulo 10).

A visualização principal é uma tabela estilo Excel (dias nas colunas,
horários nas linhas) por turma/ano letivo/semestre. Cada célula vazia vira
um link para criar uma aula; cada célula preenchida mostra a aula com
atalhos para editar ou remover. Todas as regras de conflito (professor,
turma, ambiente, disponibilidade, carga horária) são checadas por
`GradeAula.full_clean()`, chamado explicitamente antes de salvar.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DeleteView, ListView

from apps.disponibilidade.models import DiaSemana
from apps.horarios.models import Horario
from apps.turmas.models import Turma

from . import services
from .forms import GradeAulaForm
from .models import GradeAula, Semestre
from .permissions import GerenciaAcademicoMixin


def _periodo_atual(request):
    """Lê ano letivo e semestre da querystring, com valores padrão sensatos."""
    try:
        ano_letivo = int(request.GET.get('ano') or timezone.now().year)
    except (TypeError, ValueError):
        ano_letivo = timezone.now().year
    semestre = request.GET.get('semestre') or Semestre.PRIMEIRO
    if semestre not in Semestre.values:
        semestre = Semestre.PRIMEIRO
    return ano_letivo, semestre


class GradeTurmaListView(LoginRequiredMixin, GerenciaAcademicoMixin, ListView):
    """Lista turmas ativas para escolher de qual ver a grade."""
    model = Turma
    template_name = 'grade/turma_lista.html'
    context_object_name = 'turmas'
    paginate_by = 20

    def get_queryset(self):
        return Turma.objects.filter(ativo=True).order_by('serie', 'nome')

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['ano_letivo'], contexto['semestre'] = _periodo_atual(self.request)
        return contexto


class GradeVisualView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    """Grade visual (dias x horários) de uma turma, num ano letivo/semestre."""
    template_name = 'grade/visual.html'

    def get(self, request, turma_id):
        turma = get_object_or_404(Turma, pk=turma_id)
        ano_letivo, semestre = _periodo_atual(request)
        grade = services.montar_grade_turma(turma, ano_letivo, semestre)
        return render(request, self.template_name, {
            'turma': turma,
            'grade': grade,
            'dias': DiaSemana.choices,
            'ano_letivo': ano_letivo,
            'semestre': semestre,
            'semestres': Semestre.choices,
        })


class GradeAulaCreateView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    """Cria uma aula numa célula específica (turma + dia + horário + período)."""
    template_name = 'grade/aula_form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.turma = get_object_or_404(Turma, pk=kwargs['turma_id'])
        self.horario = get_object_or_404(Horario, pk=kwargs['horario_id'])
        self.dia_semana = kwargs['dia_semana']
        self.ano_letivo, self.semestre = _periodo_atual(request)

    def _contexto(self, form):
        return {
            'form': form,
            'turma': self.turma,
            'horario': self.horario,
            'dia_semana': self.dia_semana,
            'dia_rotulo': dict(DiaSemana.choices).get(self.dia_semana, self.dia_semana),
            'ano_letivo': self.ano_letivo,
            'semestre': self.semestre,
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self._contexto(GradeAulaForm()))

    def post(self, request, *args, **kwargs):
        form = GradeAulaForm(request.POST)
        if form.is_valid():
            aula = form.save(commit=False)
            aula.turma = self.turma
            aula.dia_semana = self.dia_semana
            aula.horario = self.horario
            aula.ano_letivo = self.ano_letivo
            aula.semestre = self.semestre
            aula.criado_por = request.user
            try:
                aula.full_clean()
            except ValidationError as erro:
                form.add_error(None, erro)
                return render(request, self.template_name, self._contexto(form))
            aula.save()
            messages.success(request, 'Aula adicionada à grade com sucesso.')
            return redirect(self._url_visual())
        return render(request, self.template_name, self._contexto(form))

    def _url_visual(self):
        return (
            f"{reverse('grade:visual', args=[self.turma.pk])}"
            f"?ano={self.ano_letivo}&semestre={self.semestre}"
        )


class GradeAulaUpdateView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    """Edita disciplina/professor/ambiente de uma aula já existente na grade."""
    template_name = 'grade/aula_form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.aula = get_object_or_404(GradeAula, pk=kwargs['pk'])

    def _contexto(self, form):
        return {
            'form': form,
            'turma': self.aula.turma,
            'horario': self.aula.horario,
            'dia_semana': self.aula.dia_semana,
            'dia_rotulo': self.aula.get_dia_semana_display(),
            'ano_letivo': self.aula.ano_letivo,
            'semestre': self.aula.semestre,
            'editando': True,
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self._contexto(GradeAulaForm(instance=self.aula)))

    def post(self, request, *args, **kwargs):
        form = GradeAulaForm(request.POST, instance=self.aula)
        if form.is_valid():
            aula = form.save(commit=False)
            try:
                aula.full_clean()
            except ValidationError as erro:
                form.add_error(None, erro)
                return render(request, self.template_name, self._contexto(form))
            aula.save()
            messages.success(request, 'Aula atualizada com sucesso.')
            return redirect(
                f"{reverse('grade:visual', args=[aula.turma.pk])}"
                f"?ano={aula.ano_letivo}&semestre={aula.semestre}"
            )
        return render(request, self.template_name, self._contexto(form))


class GradeAulaDeleteView(LoginRequiredMixin, GerenciaAcademicoMixin, DeleteView):
    """Remove uma aula da grade."""
    model = GradeAula
    template_name = 'grade/aula_confirmar_remocao.html'
    context_object_name = 'aula'

    def get_success_url(self):
        messages.success(self.request, 'Aula removida da grade.')
        return (
            f"{reverse('grade:visual', args=[self.object.turma_id])}"
            f"?ano={self.object.ano_letivo}&semestre={self.object.semestre}"
        )
