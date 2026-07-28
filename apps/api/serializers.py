"""
Serializers da API (Módulo 15) — um por recurso já existente no sistema.
Nenhuma regra de negócio nova é criada aqui: horários, conflitos de
grade e datas de evento reaproveitam `Model.full_clean()` via
`FullCleanMixin`; unicidades simples (matrícula, sigla, nome, ordem)
já são detectadas automaticamente pelo `ModelSerializer` a partir das
constraints do próprio modelo.
"""
from rest_framework import serializers

from apps.ambientes.models import Ambiente
from apps.calendario.models import Evento
from apps.disciplinas.models import Disciplina
from apps.disponibilidade.models import DisponibilidadeProfessor
from apps.grade.models import Atribuicao, GradeAula
from apps.horarios.models import Horario
from apps.professores.models import Professor
from apps.turmas.models import Turma
from apps.usuarios.models import Usuario

from .mixins import FullCleanMixin


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Somente leitura (o ViewSet correspondente é ReadOnly): criar/editar
    usuário envolve senha e continua exclusivo da tela web (Módulo 1),
    que já trata isso com o cuidado necessário.
    """
    papel_display = serializers.CharField(source='get_papel_display', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'matricula', 'telefone', 'papel', 'papel_display', 'ativo', 'is_active',
        ]


class ProfessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professor
        fields = [
            'id', 'nome', 'matricula', 'email', 'telefone', 'carga_horaria',
            'ativo', 'usuario', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['criado_em', 'atualizado_em']


class DisciplinaSerializer(serializers.ModelSerializer):
    tipo_ambiente_display = serializers.CharField(source='get_tipo_ambiente_display', read_only=True)

    class Meta:
        model = Disciplina
        fields = [
            'id', 'nome', 'sigla', 'quantidade_aulas_semana', 'tipo_ambiente',
            'tipo_ambiente_display', 'ativo', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['criado_em', 'atualizado_em']

    def validate_sigla(self, valor):
        return valor.strip().upper()


class TurmaSerializer(serializers.ModelSerializer):
    turno_display = serializers.CharField(source='get_turno_display', read_only=True)

    class Meta:
        model = Turma
        fields = ['id', 'nome', 'serie', 'turno', 'turno_display', 'ativo', 'criado_em', 'atualizado_em']
        read_only_fields = ['criado_em', 'atualizado_em']


class AmbienteSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Ambiente
        fields = ['id', 'nome', 'tipo', 'tipo_display', 'capacidade', 'ativo', 'criado_em', 'atualizado_em']
        read_only_fields = ['criado_em', 'atualizado_em']


class HorarioSerializer(FullCleanMixin, serializers.ModelSerializer):
    class Meta:
        model = Horario
        fields = ['id', 'ordem', 'inicio', 'fim', 'intervalo', 'ativo', 'criado_em', 'atualizado_em']
        read_only_fields = ['criado_em', 'atualizado_em']


class DisponibilidadeProfessorSerializer(serializers.ModelSerializer):
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)

    class Meta:
        model = DisponibilidadeProfessor
        fields = [
            'id', 'professor', 'dia_semana', 'dia_semana_display', 'horario',
            'disponivel', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['criado_em', 'atualizado_em']


class AtribuicaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atribuicao
        fields = ['id', 'turma', 'disciplina', 'professor', 'ativo', 'criado_em']
        read_only_fields = ['criado_em']


class GradeAulaSerializer(FullCleanMixin, serializers.ModelSerializer):
    """
    Cada aula criada/editada por aqui passa pelas mesmas regras do
    Módulo 10: turma sem choque de horário, professor sem choque de
    horário (em qualquer turma), ambiente respeitando a capacidade,
    disponibilidade do professor e carga horária semanal.
    """
    excluir_do_full_clean = ['criado_por']
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)

    class Meta:
        model = GradeAula
        fields = [
            'id', 'turma', 'disciplina', 'professor', 'ambiente', 'dia_semana',
            'dia_semana_display', 'horario', 'ano_letivo', 'semestre',
            'criado_por', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['criado_por', 'criado_em', 'atualizado_em']

    def preparar_instancia(self, instancia):
        # Usado só durante a validação (full_clean), para que as regras que
        # dependem do professor (carga horária/disponibilidade) já vejam
        # quem seria o criador — não é o que efetivamente grava no banco.
        request = self.context.get('request')
        if request is not None and request.user.is_authenticated:
            instancia.criado_por = request.user

    def create(self, validated_data):
        request = self.context.get('request')
        if request is not None and request.user.is_authenticated:
            validated_data['criado_por'] = request.user
        return super().create(validated_data)


class EventoSerializer(FullCleanMixin, serializers.ModelSerializer):
    excluir_do_full_clean = ['criado_por']
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Evento
        fields = [
            'id', 'titulo', 'tipo', 'tipo_display', 'data_inicio', 'data_fim',
            'descricao', 'afeta_aulas', 'ano_letivo', 'criado_por', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['criado_por', 'criado_em', 'atualizado_em']

    def preparar_instancia(self, instancia):
        request = self.context.get('request')
        if request is not None and request.user.is_authenticated:
            instancia.criado_por = request.user

    def create(self, validated_data):
        request = self.context.get('request')
        if request is not None and request.user.is_authenticated:
            validated_data['criado_por'] = request.user
        return super().create(validated_data)
