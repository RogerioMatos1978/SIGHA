"""
Testes do módulo Relatórios: permissões, os cálculos de cada relatório
(serviço) e as views.
"""
import datetime

from django.test import TestCase
from django.urls import reverse

from apps.ambientes.models import Ambiente, TipoAmbiente
from apps.disciplinas.models import Disciplina
from apps.disponibilidade.models import DiaSemana
from apps.grade.models import Atribuicao, GradeAula, Semestre
from apps.horarios.models import Horario
from apps.professores.models import Professor
from apps.turmas.models import Turma, Turno
from apps.usuarios.models import Papel, Usuario

from . import services


class RelatoriosPermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.secretaria = Usuario.objects.create_user(username='sec13', password=self.senha, papel=Papel.SECRETARIA)
        self.professor_user = Usuario.objects.create_user(username='prof13', password=self.senha, papel=Papel.PROFESSOR)

    def test_secretaria_acessa_home(self):
        self.client.login(username='sec13', password=self.senha)
        resposta = self.client.get(reverse('relatorios:home'))
        self.assertEqual(resposta.status_code, 200)

    def test_professor_nao_acessa_home(self):
        self.client.login(username='prof13', password=self.senha)
        resposta = self.client.get(reverse('relatorios:home'))
        self.assertEqual(resposta.status_code, 403)

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('relatorios:home'))
        self.assertEqual(resposta.status_code, 302)


class RelatoriosBaseTestCase(TestCase):
    def setUp(self):
        self.turma = Turma.objects.create(nome='1º Ano A', serie='1º Ano', turno=Turno.MATUTINO)
        self.disciplina = Disciplina.objects.create(nome='Matemática', sigla='MAT', quantidade_aulas_semana=3)
        self.professor = Professor.objects.create(nome='Ana Souza', matricula='REL001', carga_horaria=2)
        self.ambiente = Ambiente.objects.create(nome='Sala Rel', tipo=TipoAmbiente.SALA, capacidade=1)
        self.h1 = Horario.objects.create(ordem=1, inicio=datetime.time(7, 0), fim=datetime.time(7, 50))
        self.h2 = Horario.objects.create(ordem=2, inicio=datetime.time(7, 50), fim=datetime.time(8, 40))
        GradeAula.objects.create(
            turma=self.turma, disciplina=self.disciplina, professor=self.professor, ambiente=self.ambiente,
            dia_semana=DiaSemana.SEGUNDA, horario=self.h1, ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )


class ServicesTests(RelatoriosBaseTestCase):
    def test_grade_semanal_do_professor_mostra_aula_lancada(self):
        grade = services.grade_semanal_do_professor(self.professor, 2026, Semestre.PRIMEIRO)
        aula = grade[self.h1][DiaSemana.SEGUNDA]
        self.assertIsNotNone(aula)
        self.assertEqual(aula.turma, self.turma)
        self.assertIsNone(grade[self.h2][DiaSemana.SEGUNDA])

    def test_carga_horaria_calcula_percentual(self):
        linhas = services.relatorio_carga_horaria(2026, Semestre.PRIMEIRO)
        linha = next(l for l in linhas if l['professor'] == self.professor)
        self.assertEqual(linha['alocadas'], 1)
        self.assertEqual(linha['maximo'], 2)
        self.assertEqual(linha['livres'], 1)
        self.assertEqual(linha['percentual'], 50.0)

    def test_ocupacao_ambientes_calcula_percentual(self):
        linhas = services.relatorio_ocupacao_ambientes(2026, Semestre.PRIMEIRO)
        linha = next(l for l in linhas if l['ambiente'] == self.ambiente)
        # 2 horarios ativos x 5 dias x capacidade 1 = 10 slots; 1 aula alocada = 10%
        self.assertEqual(linha['capacidade_total'], 10)
        self.assertEqual(linha['alocadas'], 1)
        self.assertEqual(linha['percentual'], 10.0)

    def test_pendencias_mostra_turma_incompleta(self):
        Atribuicao.objects.create(turma=self.turma, disciplina=self.disciplina, professor=self.professor)
        linhas = services.relatorio_pendencias_por_turma(2026, Semestre.PRIMEIRO)
        linha = next(l for l in linhas if l['turma'] == self.turma)
        self.assertEqual(linha['necessarias'], 3)
        self.assertEqual(linha['alocadas'], 1)
        self.assertEqual(linha['faltantes'], 2)
        self.assertFalse(linha['completa'])

    def test_pendencias_ignora_turma_sem_atribuicao(self):
        linhas = services.relatorio_pendencias_por_turma(2026, Semestre.PRIMEIRO)
        self.assertEqual(linhas, [])


class ViewsTests(RelatoriosBaseTestCase):
    def setUp(self):
        super().setUp()
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin13', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin13', password=self.senha)

    def test_home(self):
        resposta = self.client.get(reverse('relatorios:home'))
        self.assertEqual(resposta.status_code, 200)

    def test_grade_professor_sem_selecao(self):
        resposta = self.client.get(reverse('relatorios:grade_professor'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Ana Souza')

    def test_grade_professor_com_selecao_mostra_aula(self):
        resposta = self.client.get(reverse('relatorios:grade_professor'), {
            'professor': self.professor.pk, 'ano': 2026, 'semestre': '1',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, self.disciplina.sigla)

    def test_carga_horaria_view(self):
        resposta = self.client.get(reverse('relatorios:carga_horaria'), {'ano': 2026, 'semestre': '1'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Ana Souza')

    def test_ocupacao_ambientes_view(self):
        resposta = self.client.get(reverse('relatorios:ocupacao_ambientes'), {'ano': 2026, 'semestre': '1'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Sala Rel')

    def test_pendencias_view(self):
        Atribuicao.objects.create(turma=self.turma, disciplina=self.disciplina, professor=self.professor)
        resposta = self.client.get(reverse('relatorios:pendencias'), {'ano': 2026, 'semestre': '1'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, '1º Ano A')
