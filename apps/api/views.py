"""
ViewSets da API (Módulo 15). Cada um expõe um recurso já existente no
sistema; a única regra de autorização nova é o mapeamento para
`PermiteGerenciarAcademico` / `PermiteGerenciarUsuarios`, que só espelha
o que as telas web (Módulos 1-13) já fazem.
"""
from rest_framework import viewsets

from apps.ambientes.models import Ambiente
from apps.calendario.models import Evento
from apps.disciplinas.models import Disciplina
from apps.disponibilidade.models import DisponibilidadeProfessor
from apps.grade.models import Atribuicao, GradeAula
from apps.horarios.models import Horario
from apps.professores.models import Professor
from apps.substituicoes.models import Substituicao
from apps.turmas.models import Turma
from apps.usuarios.models import Usuario

from . import serializers
from .permissions import PermiteGerenciarAcademico, PermiteGerenciarUsuarios


def _filtrar_por_booleano(queryset, request, campo):
    valor = request.query_params.get(campo)
    if valor is None:
        return queryset
    return queryset.filter(**{campo: valor.lower() in ('1', 'true', 'sim')})


def _filtrar_por_igualdade(queryset, request, campos):
    for campo in campos:
        valor = request.query_params.get(campo)
        if valor:
            queryset = queryset.filter(**{campo: valor})
    return queryset


class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Somente leitura: criar/editar usuário envolve senha e continua
    exclusivo da tela web (Módulo 1).
    """
    queryset = Usuario.objects.all().order_by('username')
    serializer_class = serializers.UsuarioSerializer
    permission_classes = [PermiteGerenciarUsuarios]


class ProfessorViewSet(viewsets.ModelViewSet):
    queryset = Professor.objects.all().order_by('nome')
    serializer_class = serializers.ProfessorSerializer
    permission_classes = [PermiteGerenciarAcademico]

    def get_queryset(self):
        return _filtrar_por_booleano(super().get_queryset(), self.request, 'ativo')


class DisciplinaViewSet(viewsets.ModelViewSet):
    queryset = Disciplina.objects.all().order_by('nome')
    serializer_class = serializers.DisciplinaSerializer
    permission_classes = [PermiteGerenciarAcademico]

    def get_queryset(self):
        return _filtrar_por_booleano(super().get_queryset(), self.request, 'ativo')


class TurmaViewSet(viewsets.ModelViewSet):
    queryset = Turma.objects.all().order_by('serie', 'nome')
    serializer_class = serializers.TurmaSerializer
    permission_classes = [PermiteGerenciarAcademico]

    def get_queryset(self):
        qs = _filtrar_por_booleano(super().get_queryset(), self.request, 'ativo')
        return _filtrar_por_igualdade(qs, self.request, ['turno', 'etapa_ensino', 'curso_tecnico'])


class AmbienteViewSet(viewsets.ModelViewSet):
    queryset = Ambiente.objects.all().order_by('tipo', 'nome')
    serializer_class = serializers.AmbienteSerializer
    permission_classes = [PermiteGerenciarAcademico]

    def get_queryset(self):
        qs = _filtrar_por_booleano(super().get_queryset(), self.request, 'ativo')
        return _filtrar_por_igualdade(qs, self.request, ['tipo'])


class HorarioViewSet(viewsets.ModelViewSet):
    queryset = Horario.objects.all().order_by('ordem')
    serializer_class = serializers.HorarioSerializer
    permission_classes = [PermiteGerenciarAcademico]

    def get_queryset(self):
        return _filtrar_por_booleano(super().get_queryset(), self.request, 'ativo')


class DisponibilidadeProfessorViewSet(viewsets.ModelViewSet):
    queryset = DisponibilidadeProfessor.objects.select_related('professor', 'horario').all()
    serializer_class = serializers.DisponibilidadeProfessorSerializer
    permission_classes = [PermiteGerenciarAcademico]

    def get_queryset(self):
        return _filtrar_por_igualdade(super().get_queryset(), self.request, ['professor', 'dia_semana', 'disponivel'])


class AtribuicaoViewSet(viewsets.ModelViewSet):
    queryset = Atribuicao.objects.select_related('turma', 'disciplina', 'professor').all()
    serializer_class = serializers.AtribuicaoSerializer
    permission_classes = [PermiteGerenciarAcademico]

    def get_queryset(self):
        return _filtrar_por_igualdade(super().get_queryset(), self.request, ['turma', 'disciplina', 'professor'])


class GradeAulaViewSet(viewsets.ModelViewSet):
    queryset = GradeAula.objects.select_related('turma', 'disciplina', 'professor', 'ambiente', 'horario').all()
    serializer_class = serializers.GradeAulaSerializer
    permission_classes = [PermiteGerenciarAcademico]

    def get_queryset(self):
        return _filtrar_por_igualdade(
            super().get_queryset(),
            self.request,
            ['turma', 'professor', 'ambiente', 'ano_letivo', 'semestre', 'dia_semana'],
        )


class SubstituicaoViewSet(viewsets.ModelViewSet):
    queryset = Substituicao.objects.select_related('aula__turma', 'professor_substituto').all()
    serializer_class = serializers.SubstituicaoSerializer
    permission_classes = [PermiteGerenciarAcademico]

    def get_queryset(self):
        return _filtrar_por_igualdade(super().get_queryset(), self.request, ['aula', 'professor_substituto', 'data'])


class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = serializers.EventoSerializer
    permission_classes = [PermiteGerenciarAcademico]

    def get_queryset(self):
        return _filtrar_por_igualdade(super().get_queryset(), self.request, ['tipo', 'ano_letivo', 'afeta_aulas'])
