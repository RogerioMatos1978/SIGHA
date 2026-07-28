"""
Views do módulo Relatórios (Módulo 13): todas somente leitura, a partir
da grade já montada (Módulo 10) e das atribuições (Módulo 11).
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from apps.disponibilidade.models import DiaSemana
from apps.grade.models import Semestre
from apps.professores.models import Professor

from . import services
from .permissions import GerenciaAcademicoMixin


def _periodo_atual(request):
    try:
        ano_letivo = int(request.GET.get('ano') or timezone.now().year)
    except (TypeError, ValueError):
        ano_letivo = timezone.now().year
    semestre = request.GET.get('semestre') or Semestre.PRIMEIRO
    if semestre not in Semestre.values:
        semestre = Semestre.PRIMEIRO
    return ano_letivo, semestre


class RelatoriosHomeView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    """Painel com links para cada relatório disponível."""
    template_name = 'relatorios/home.html'

    def get(self, request):
        ano_letivo, semestre = _periodo_atual(request)
        return render(request, self.template_name, {'ano_letivo': ano_letivo, 'semestre': semestre})


class RelatorioGradeProfessorView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    """Grade semanal de um professor específico, em todas as turmas que ele leciona."""
    template_name = 'relatorios/grade_professor.html'

    def get(self, request):
        ano_letivo, semestre = _periodo_atual(request)
        professores = Professor.objects.filter(ativo=True).order_by('nome')
        professor = None
        grade = None
        professor_id = request.GET.get('professor')
        if professor_id:
            professor = get_object_or_404(Professor, pk=professor_id)
            grade = services.grade_semanal_do_professor(professor, ano_letivo, semestre)
        return render(request, self.template_name, {
            'professores': professores, 'professor': professor, 'grade': grade,
            'dias': DiaSemana.choices, 'ano_letivo': ano_letivo, 'semestre': semestre,
        })


class RelatorioCargaHorariaView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    """Ocupação da carga horária semanal de cada professor ativo."""
    template_name = 'relatorios/carga_horaria.html'

    def get(self, request):
        ano_letivo, semestre = _periodo_atual(request)
        linhas = services.relatorio_carga_horaria(ano_letivo, semestre)
        return render(request, self.template_name, {
            'linhas': linhas, 'ano_letivo': ano_letivo, 'semestre': semestre,
        })


class RelatorioOcupacaoAmbientesView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    """Ocupação de cada ambiente ativo em relação à capacidade total de slots."""
    template_name = 'relatorios/ocupacao_ambientes.html'

    def get(self, request):
        ano_letivo, semestre = _periodo_atual(request)
        linhas = services.relatorio_ocupacao_ambientes(ano_letivo, semestre)
        return render(request, self.template_name, {
            'linhas': linhas, 'ano_letivo': ano_letivo, 'semestre': semestre,
        })


class RelatorioPendenciasView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    """Quanto falta para completar a grade de cada turma com atribuições cadastradas."""
    template_name = 'relatorios/pendencias.html'

    def get(self, request):
        ano_letivo, semestre = _periodo_atual(request)
        linhas = services.relatorio_pendencias_por_turma(ano_letivo, semestre)
        return render(request, self.template_name, {
            'linhas': linhas, 'ano_letivo': ano_letivo, 'semestre': semestre,
        })
