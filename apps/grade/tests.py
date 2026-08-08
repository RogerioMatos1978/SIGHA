"""
Testes do módulo Grade: permissões e as regras obrigatórias de conflito
(professor, turma, ambiente, disponibilidade, carga horária).
"""
import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.ambientes.models import Ambiente, TipoAmbiente
from apps.disciplinas.models import Disciplina
from apps.disponibilidade.models import DiaSemana, DisponibilidadeProfessor
from apps.horarios.models import Horario
from apps.professores.models import Professor
from apps.turmas.models import EtapaEnsino, Turma, Turno
from apps.usuarios.models import Papel, Usuario

from .models import Atribuicao, GradeAula, Semestre


class GradeBaseTestCase(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin10', password=self.senha, papel=Papel.ADMINISTRADOR)

        self.turma_a = Turma.objects.create(nome='1º Ano A', serie='1º Ano', turno=Turno.MATUTINO)
        self.turma_b = Turma.objects.create(nome='1º Ano B', serie='1º Ano', turno=Turno.MATUTINO)
        self.disciplina = Disciplina.objects.create(nome='Matemática', sigla='MAT', quantidade_aulas_semana=5)
        self.professor = Professor.objects.create(nome='Ana Souza', matricula='PROF001', carga_horaria=20)
        self.outro_professor = Professor.objects.create(nome='Bruno Lima', matricula='PROF002', carga_horaria=20)
        self.ambiente = Ambiente.objects.create(nome='Sala 1', tipo=TipoAmbiente.SALA, capacidade=1)
        self.h1 = Horario.objects.create(ordem=1, inicio=datetime.time(7, 0), fim=datetime.time(7, 50))
        self.h2 = Horario.objects.create(ordem=2, inicio=datetime.time(7, 50), fim=datetime.time(8, 40))

    def criar_aula(self, **overrides):
        dados = dict(
            turma=self.turma_a, disciplina=self.disciplina, professor=self.professor,
            ambiente=self.ambiente, dia_semana=DiaSemana.SEGUNDA, horario=self.h1,
            ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        dados.update(overrides)
        aula = GradeAula(**dados)
        aula.full_clean()
        aula.save()
        return aula


class GradePermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.secretaria = Usuario.objects.create_user(username='sec10', password=self.senha, papel=Papel.SECRETARIA)
        self.professor_user = Usuario.objects.create_user(username='prof10', password=self.senha, papel=Papel.PROFESSOR)

    def test_secretaria_acessa_lista(self):
        self.client.login(username='sec10', password=self.senha)
        resposta = self.client.get(reverse('grade:lista'))
        self.assertEqual(resposta.status_code, 200)

    def test_professor_nao_acessa_lista(self):
        self.client.login(username='prof10', password=self.senha)
        resposta = self.client.get(reverse('grade:lista'))
        self.assertEqual(resposta.status_code, 403)

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('grade:lista'))
        self.assertEqual(resposta.status_code, 302)


class GradeRegrasDeConflitoTests(GradeBaseTestCase):
    def test_criar_aula_valida(self):
        aula = self.criar_aula()
        self.assertEqual(GradeAula.objects.count(), 1)
        self.assertEqual(aula.turma, self.turma_a)

    def test_turma_nao_pode_ter_duas_aulas_no_mesmo_horario(self):
        self.criar_aula()
        segunda_aula = GradeAula(
            turma=self.turma_a, disciplina=self.disciplina, professor=self.outro_professor,
            ambiente=self.ambiente, dia_semana=DiaSemana.SEGUNDA, horario=self.h1,
            ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        with self.assertRaises(ValidationError):
            segunda_aula.full_clean()

    def test_professor_nao_pode_estar_em_duas_turmas_ao_mesmo_tempo(self):
        self.criar_aula()
        segunda_aula = GradeAula(
            turma=self.turma_b, disciplina=self.disciplina, professor=self.professor,
            ambiente=self.ambiente, dia_semana=DiaSemana.SEGUNDA, horario=self.h1,
            ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        with self.assertRaises(ValidationError):
            segunda_aula.full_clean()

    def test_ambiente_respeita_capacidade_de_uso_simultaneo(self):
        self.criar_aula()  # ocupa a Sala 1 (capacidade=1) na segunda, horário 1
        segunda_aula = GradeAula(
            turma=self.turma_b, disciplina=self.disciplina, professor=self.outro_professor,
            ambiente=self.ambiente, dia_semana=DiaSemana.SEGUNDA, horario=self.h1,
            ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        with self.assertRaises(ValidationError) as contexto:
            segunda_aula.full_clean()
        self.assertIn('ambiente', contexto.exception.message_dict)

    def test_ambiente_com_capacidade_maior_que_um_permite_uso_simultaneo(self):
        laboratorio = Ambiente.objects.create(nome='Laboratório', tipo=TipoAmbiente.LABORATORIO, capacidade=2)
        self.criar_aula(ambiente=laboratorio)
        segunda_aula = GradeAula(
            turma=self.turma_b, disciplina=self.disciplina, professor=self.outro_professor,
            ambiente=laboratorio, dia_semana=DiaSemana.SEGUNDA, horario=self.h1,
            ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        segunda_aula.full_clean()  # não deve levantar erro
        segunda_aula.save()
        self.assertEqual(GradeAula.objects.filter(ambiente=laboratorio).count(), 2)

    def test_respeita_indisponibilidade_do_professor(self):
        DisponibilidadeProfessor.objects.create(
            professor=self.professor, dia_semana=DiaSemana.SEGUNDA, horario=self.h1, disponivel=False,
        )
        aula = GradeAula(
            turma=self.turma_a, disciplina=self.disciplina, professor=self.professor,
            ambiente=self.ambiente, dia_semana=DiaSemana.SEGUNDA, horario=self.h1,
            ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        with self.assertRaises(ValidationError) as contexto:
            aula.full_clean()
        self.assertIn('professor', contexto.exception.message_dict)

    def test_nao_ultrapassa_carga_horaria_do_professor(self):
        self.professor.carga_horaria = 1
        self.professor.save()
        self.criar_aula()  # 1ª aula, dentro do limite
        segunda_aula = GradeAula(
            turma=self.turma_b, disciplina=self.disciplina, professor=self.professor,
            ambiente=Ambiente.objects.create(nome='Sala 2', tipo=TipoAmbiente.SALA, capacidade=1),
            dia_semana=DiaSemana.SEGUNDA, horario=self.h2,
            ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        with self.assertRaises(ValidationError) as contexto:
            segunda_aula.full_clean()
        self.assertIn('professor', contexto.exception.message_dict)

    def test_mesmo_professor_pode_dar_aula_em_semestre_diferente(self):
        self.professor.carga_horaria = 1
        self.professor.save()
        self.criar_aula(semestre=Semestre.PRIMEIRO)
        segunda_aula = GradeAula(
            turma=self.turma_a, disciplina=self.disciplina, professor=self.professor,
            ambiente=self.ambiente, dia_semana=DiaSemana.SEGUNDA, horario=self.h1,
            ano_letivo=2026, semestre=Semestre.SEGUNDO,
        )
        segunda_aula.full_clean()  # outro semestre, carga horária reinicia


class GradeViewsTests(GradeBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username='admin10', password=self.senha)

    def test_grade_visual_mostra_celulas_vazias_para_turma_sem_aulas(self):
        resposta = self.client.get(reverse('grade:visual', args=[self.turma_a.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'bi-plus-lg')  # botão de adicionar aula na célula vazia

    def test_criar_aula_via_post(self):
        url = reverse('grade:criar', args=[self.turma_a.pk, DiaSemana.SEGUNDA, self.h1.pk])
        resposta = self.client.post(url, {
            'disciplina': self.disciplina.pk,
            'professor': self.professor.pk,
            'ambiente': self.ambiente.pk,
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(GradeAula.objects.count(), 1)

    def test_criar_aula_conflitante_via_post_mostra_erro(self):
        self.criar_aula()
        url = reverse('grade:criar', args=[self.turma_b.pk, DiaSemana.SEGUNDA, self.h1.pk])
        resposta = self.client.post(url, {
            'disciplina': self.disciplina.pk,
            'professor': self.professor.pk,
            'ambiente': Ambiente.objects.create(nome='Sala 3', tipo=TipoAmbiente.SALA).pk,
        })
        self.assertEqual(resposta.status_code, 200)  # re-renderiza o formulário com erro
        self.assertEqual(GradeAula.objects.count(), 1)  # não criou a segunda

    def test_remover_aula(self):
        aula = self.criar_aula()
        resposta = self.client.post(reverse('grade:remover', args=[aula.pk]))
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(GradeAula.objects.count(), 0)

    def test_editar_aula(self):
        aula = self.criar_aula()
        resposta = self.client.post(reverse('grade:editar', args=[aula.pk]), {
            'disciplina': self.disciplina.pk,
            'professor': self.outro_professor.pk,
            'ambiente': self.ambiente.pk,
        })
        self.assertEqual(resposta.status_code, 302)
        aula.refresh_from_db()
        self.assertEqual(aula.professor, self.outro_professor)


class AtribuicaoTests(GradeBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username='admin10', password=self.senha)

    def test_criar_atribuicao(self):
        resposta = self.client.post(reverse('grade:atribuicao_criar', args=[self.turma_a.pk]), {
            'disciplina': self.disciplina.pk,
            'professor': self.professor.pk,
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Atribuicao.objects.count(), 1)

    def test_nao_permite_duas_atribuicoes_para_mesma_disciplina_na_mesma_turma(self):
        Atribuicao.objects.create(turma=self.turma_a, disciplina=self.disciplina, professor=self.professor)
        duplicada = Atribuicao(turma=self.turma_a, disciplina=self.disciplina, professor=self.outro_professor)
        with self.assertRaises(ValidationError):
            duplicada.full_clean()

    def test_listar_atribuicoes(self):
        Atribuicao.objects.create(turma=self.turma_a, disciplina=self.disciplina, professor=self.professor)
        resposta = self.client.get(reverse('grade:atribuicoes', args=[self.turma_a.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, self.professor.nome)

    def test_remover_atribuicao(self):
        atribuicao = Atribuicao.objects.create(turma=self.turma_a, disciplina=self.disciplina, professor=self.professor)
        resposta = self.client.post(reverse('grade:atribuicao_remover', args=[atribuicao.pk]))
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Atribuicao.objects.count(), 0)

    def test_editar_atribuicao_troca_professor_permanentemente(self):
        atribuicao = Atribuicao.objects.create(turma=self.turma_a, disciplina=self.disciplina, professor=self.professor)
        resposta = self.client.post(reverse('grade:atribuicao_editar', args=[atribuicao.pk]), {
            'disciplina': self.disciplina.pk,
            'professor': self.outro_professor.pk,
        })
        self.assertEqual(resposta.status_code, 302)
        atribuicao.refresh_from_db()
        self.assertEqual(atribuicao.professor, self.outro_professor)


class AtribuicaoVinculoEtapaTests(GradeBaseTestCase):
    """
    Módulo 19: professor fora da etapa/turma autorizada gera só um AVISO
    (messages.warning) — a atribuição/aula é salva normalmente mesmo assim.
    """
    def setUp(self):
        super().setUp()
        self.client.login(username='admin10', password=self.senha)
        # turma_a usa o padrão FUNDAMENTAL_2 (ver Turma.etapa_ensino); este
        # professor só está autorizado para o Médio — fora do vínculo, de propósito.
        self.professor.etapas_autorizadas = [EtapaEnsino.MEDIO]
        self.professor.save()

    def test_criar_atribuicao_fora_do_vinculo_salva_com_aviso(self):
        resposta = self.client.post(reverse('grade:atribuicao_criar', args=[self.turma_a.pk]), {
            'disciplina': self.disciplina.pk, 'professor': self.professor.pk,
        }, follow=True)
        self.assertEqual(Atribuicao.objects.count(), 1)
        mensagens = [str(m) for m in resposta.context['messages']]
        self.assertTrue(any('não está vinculado' in m for m in mensagens))

    def test_gerenciar_academico_ve_aviso_na_tela_de_gerar_grade(self):
        Atribuicao.objects.create(turma=self.turma_a, disciplina=self.disciplina, professor=self.professor)
        resposta = self.client.get(reverse('algoritmo:gerar', args=[self.turma_a.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'fora da etapa/turma autorizada')
