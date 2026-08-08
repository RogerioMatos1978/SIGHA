"""
Testes do módulo Substituições (Módulo 19): regras de validação do
modelo (data precisa cair no dia da semana certo, substituto xor aula
cancelada, sem choque de horário) e o fluxo de criar/remover pela tela.
"""
import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.ambientes.models import Ambiente, TipoAmbiente
from apps.disciplinas.models import Disciplina
from apps.disponibilidade.models import DiaSemana
from apps.grade.models import GradeAula, Semestre
from apps.horarios.models import Horario
from apps.professores.models import Professor
from apps.turmas.models import Turma, Turno
from apps.usuarios.models import Papel, Usuario

from .models import Substituicao

SEGUNDA_10_08_2026 = datetime.date(2026, 8, 10)  # segunda-feira de verdade
TERCA_11_08_2026 = datetime.date(2026, 8, 11)  # terça-feira — dia da semana errado de propósito
SABADO_08_08_2026 = datetime.date(2026, 8, 8)  # cai num fim de semana, de propósito


class SubstituicaoBaseTestCase(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin19', password=self.senha, papel=Papel.ADMINISTRADOR)

        self.turma = Turma.objects.create(nome='1º Ano A', serie='1º Ano', turno=Turno.MATUTINO)
        self.turma_b = Turma.objects.create(nome='1º Ano B', serie='1º Ano', turno=Turno.MATUTINO)
        self.disciplina = Disciplina.objects.create(nome='Matemática', sigla='MAT19', quantidade_aulas_semana=5)
        self.titular = Professor.objects.create(nome='Ana Titular', matricula='SUB001', carga_horaria=20)
        self.substituto = Professor.objects.create(nome='Bruno Substituto', matricula='SUB002', carga_horaria=20)
        self.outro_titular = Professor.objects.create(nome='Carla Titular', matricula='SUB003', carga_horaria=20)
        self.ambiente = Ambiente.objects.create(nome='Sala Sub', tipo=TipoAmbiente.SALA, capacidade=1)
        self.horario = Horario.objects.create(ordem=1, inicio=datetime.time(7, 0), fim=datetime.time(7, 50))

        self.aula = GradeAula.objects.create(
            turma=self.turma, disciplina=self.disciplina, professor=self.titular, ambiente=self.ambiente,
            dia_semana=DiaSemana.SEGUNDA, horario=self.horario, ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )


class SubstituicaoModeloTests(SubstituicaoBaseTestCase):
    def test_criar_substituicao_valida(self):
        substituicao = Substituicao(aula=self.aula, data=SEGUNDA_10_08_2026, professor_substituto=self.substituto)
        substituicao.full_clean()
        substituicao.save()
        self.assertEqual(Substituicao.objects.count(), 1)

    def test_aula_cancelada_sem_substituto_e_valida(self):
        substituicao = Substituicao(aula=self.aula, data=SEGUNDA_10_08_2026, aula_cancelada=True)
        substituicao.full_clean()
        substituicao.save()
        self.assertTrue(Substituicao.objects.get().aula_cancelada)

    def test_precisa_de_substituto_ou_cancelamento(self):
        substituicao = Substituicao(aula=self.aula, data=SEGUNDA_10_08_2026)
        with self.assertRaises(ValidationError) as contexto:
            substituicao.full_clean()
        self.assertIn('professor_substituto', contexto.exception.message_dict)

    def test_nao_pode_ter_substituto_e_cancelamento_juntos(self):
        substituicao = Substituicao(
            aula=self.aula, data=SEGUNDA_10_08_2026, professor_substituto=self.substituto, aula_cancelada=True,
        )
        with self.assertRaises(ValidationError) as contexto:
            substituicao.full_clean()
        self.assertIn('aula_cancelada', contexto.exception.message_dict)

    def test_data_precisa_cair_no_dia_da_semana_da_aula(self):
        substituicao = Substituicao(aula=self.aula, data=TERCA_11_08_2026, professor_substituto=self.substituto)
        with self.assertRaises(ValidationError) as contexto:
            substituicao.full_clean()
        self.assertIn('data', contexto.exception.message_dict)

    def test_data_de_fim_de_semana_e_rejeitada(self):
        substituicao = Substituicao(aula=self.aula, data=SABADO_08_08_2026, professor_substituto=self.substituto)
        with self.assertRaises(ValidationError):
            substituicao.full_clean()

    def test_substituto_nao_pode_ser_o_proprio_titular(self):
        substituicao = Substituicao(aula=self.aula, data=SEGUNDA_10_08_2026, professor_substituto=self.titular)
        with self.assertRaises(ValidationError) as contexto:
            substituicao.full_clean()
        self.assertIn('professor_substituto', contexto.exception.message_dict)

    def test_substituto_com_choque_na_grade_regular_e_rejeitado(self):
        # o substituto já dá aula normalmente nesse mesmo horário, noutra turma
        GradeAula.objects.create(
            turma=self.turma_b, disciplina=self.disciplina, professor=self.substituto, ambiente=self.ambiente,
            dia_semana=DiaSemana.SEGUNDA, horario=self.horario, ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        substituicao = Substituicao(aula=self.aula, data=SEGUNDA_10_08_2026, professor_substituto=self.substituto)
        with self.assertRaises(ValidationError) as contexto:
            substituicao.full_clean()
        self.assertIn('professor_substituto', contexto.exception.message_dict)

    def test_substituto_com_choque_em_outra_substituicao_e_rejeitado(self):
        outra_aula = GradeAula.objects.create(
            turma=self.turma_b, disciplina=self.disciplina, professor=self.outro_titular, ambiente=self.ambiente,
            dia_semana=DiaSemana.SEGUNDA, horario=self.horario, ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        Substituicao.objects.create(aula=outra_aula, data=SEGUNDA_10_08_2026, professor_substituto=self.substituto)
        substituicao = Substituicao(aula=self.aula, data=SEGUNDA_10_08_2026, professor_substituto=self.substituto)
        with self.assertRaises(ValidationError) as contexto:
            substituicao.full_clean()
        self.assertIn('professor_substituto', contexto.exception.message_dict)

    def test_nao_permite_duas_substituicoes_para_mesma_aula_e_data(self):
        Substituicao.objects.create(aula=self.aula, data=SEGUNDA_10_08_2026, professor_substituto=self.substituto)
        with self.assertRaises(Exception):
            Substituicao.objects.create(aula=self.aula, data=SEGUNDA_10_08_2026, professor_substituto=self.titular)


class SubstituicaoViewTests(SubstituicaoBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username='admin19', password=self.senha)

    def test_criar_substituicao_pela_tela(self):
        resposta = self.client.post(reverse('substituicoes:criar', args=[self.aula.pk]), {
            'data': SEGUNDA_10_08_2026, 'professor_substituto': self.substituto.pk,
        })
        self.assertEqual(resposta.status_code, 302, resposta.content)
        self.assertEqual(Substituicao.objects.count(), 1)

    def test_lista_mostra_substituicao_criada(self):
        Substituicao.objects.create(aula=self.aula, data=SEGUNDA_10_08_2026, professor_substituto=self.substituto)
        resposta = self.client.get(reverse('substituicoes:lista'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Bruno Substituto')

    def test_remover_substituicao(self):
        substituicao = Substituicao.objects.create(
            aula=self.aula, data=SEGUNDA_10_08_2026, professor_substituto=self.substituto,
        )
        resposta = self.client.post(reverse('substituicoes:remover', args=[substituicao.pk]))
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Substituicao.objects.count(), 0)

    def test_professor_nao_acessa(self):
        self.client.logout()
        Usuario.objects.create_user(username='prof19', password=self.senha, papel=Papel.PROFESSOR)
        self.client.login(username='prof19', password=self.senha)
        resposta = self.client.get(reverse('substituicoes:lista'))
        self.assertEqual(resposta.status_code, 403)
