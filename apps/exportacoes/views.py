"""
Views do módulo Exportações (Módulo 14): baixam a Grade de uma turma ou
de um professor em Excel, PDF, Word, PNG ou JPEG.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from django.views import View

from apps.disponibilidade.models import DiaSemana
from apps.grade.models import Semestre
from apps.grade import services as grade_services
from apps.professores.models import Professor
from apps.relatorios import services as relatorios_services
from apps.turmas.models import Turma

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


def _responder_arquivo(formato, titulo, dias, grid, montar_linhas, nome_base):
    try:
        buffer, content_type, extensao = services.gerar_arquivo(formato, titulo, dias, grid, montar_linhas)
    except ValidationError as erro:
        return HttpResponseBadRequest(str(erro))

    nome_arquivo = f'{slugify(nome_base)}.{extensao}'
    resposta = HttpResponse(buffer.getvalue(), content_type=content_type)
    resposta['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
    return resposta


class ExportarGradeTurmaView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    def get(self, request, turma_id, formato):
        turma = get_object_or_404(Turma, pk=turma_id)
        ano_letivo, semestre = _periodo_atual(request)
        grid = grade_services.montar_grade_turma(turma, ano_letivo, semestre)
        titulo = f'Grade — {turma.nome} ({ano_letivo}, {semestre}º semestre)'
        return _responder_arquivo(
            formato, titulo, DiaSemana.choices, grid, services.linhas_celula_turma,
            nome_base=f'grade-{turma.nome}-{ano_letivo}-{semestre}',
        )


class ExportarGradeProfessorView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    def get(self, request, professor_id, formato):
        professor = get_object_or_404(Professor, pk=professor_id)
        ano_letivo, semestre = _periodo_atual(request)
        grid = relatorios_services.grade_semanal_do_professor(professor, ano_letivo, semestre)
        titulo = f'Grade — {professor.nome} ({ano_letivo}, {semestre}º semestre)'
        return _responder_arquivo(
            formato, titulo, DiaSemana.choices, grid, services.linhas_celula_professor,
            nome_base=f'grade-{professor.nome}-{ano_letivo}-{semestre}',
        )
