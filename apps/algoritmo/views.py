"""
Views do módulo Algoritmo automático (Módulo 11).

Uma tela de confirmação mostra o que será gerado (a partir das
atribuições cadastradas no Módulo 10); ao confirmar, o solver roda e cada
proposta é salva através de `GradeAula.full_clean()`, reaproveitando toda
a validação de conflito já existente. O resultado (quantas aulas foram
criadas, o que ficou faltando, o que não teve ambiente disponível) é
mostrado numa tela de relatório.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from apps.grade.models import GradeAula, Semestre
from apps.turmas.models import Turma

from . import solver
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


class AlgoritmoTurmaListView(LoginRequiredMixin, GerenciaAcademicoMixin, ListView):
    """Lista turmas ativas para escolher de qual gerar a grade automaticamente."""
    model = Turma
    template_name = 'algoritmo/turma_lista.html'
    context_object_name = 'turmas'
    paginate_by = 20

    def get_queryset(self):
        return Turma.objects.filter(ativo=True).order_by('serie', 'nome')


class GerarGradeView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    """GET mostra o que será gerado; POST roda o solver e salva o resultado."""
    template_name = 'algoritmo/gerar.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.turma = get_object_or_404(Turma, pk=kwargs['turma_id'])

    def get(self, request, *args, **kwargs):
        ano_letivo, semestre = _periodo_atual(request)
        resumo = solver.resumo_atribuicoes(self.turma, ano_letivo, semestre)
        return render(request, self.template_name, {
            'turma': self.turma, 'resumo': resumo,
            'ano_letivo': ano_letivo, 'semestre': semestre,
        })

    def post(self, request, *args, **kwargs):
        ano_letivo, semestre = _periodo_atual(request)

        if request.POST.get('limpar_existentes'):
            GradeAula.objects.filter(turma=self.turma, ano_letivo=ano_letivo, semestre=semestre).delete()

        resultado = solver.gerar_propostas_para_turma(self.turma, ano_letivo, semestre)

        criadas = 0
        falhas = []
        for proposta in resultado['propostas']:
            aula = GradeAula(
                turma=proposta['turma'], disciplina=proposta['disciplina'], professor=proposta['professor'],
                ambiente=proposta['ambiente'], dia_semana=proposta['dia_semana'], horario=proposta['horario'],
                ano_letivo=ano_letivo, semestre=semestre, criado_por=request.user,
            )
            try:
                aula.full_clean()
            except ValidationError as erro:
                falhas.append({'proposta': proposta, 'erro': erro})
                continue
            aula.save()
            criadas += 1

        messages.success(request, f'{criadas} aula(s) gerada(s) automaticamente para {self.turma.nome}.')
        return render(request, 'algoritmo/resultado.html', {
            'turma': self.turma, 'ano_letivo': ano_letivo, 'semestre': semestre,
            'criadas': criadas, 'incompletas': resultado['incompletas'],
            'sem_ambiente': resultado['sem_ambiente'], 'falhas': falhas,
        })
