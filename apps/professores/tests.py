"""
Testes do módulo Professores: permissões de acesso, CRUD básico e o
vínculo Professor↔Turma do Módulo 19 (etapa de ensino + exceções).
"""
from django.test import TestCase
from django.urls import reverse

from apps.turmas.models import EtapaEnsino, Turma, Turno
from apps.usuarios.models import Usuario, Papel
from .models import Professor


class ProfessorPermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.secretaria = Usuario.objects.create_user(username='sec1', password=self.senha, papel=Papel.SECRETARIA)
        self.professor_user = Usuario.objects.create_user(username='prof1', password=self.senha, papel=Papel.PROFESSOR)

    def test_secretaria_acessa_lista(self):
        self.client.login(username='sec1', password=self.senha)
        resposta = self.client.get(reverse('professores:lista'))
        self.assertEqual(resposta.status_code, 200)

    def test_professor_nao_acessa_lista(self):
        self.client.login(username='prof1', password=self.senha)
        resposta = self.client.get(reverse('professores:lista'))
        self.assertEqual(resposta.status_code, 403)

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('professores:lista'))
        self.assertEqual(resposta.status_code, 302)


class ProfessorCrudTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin3', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin3', password=self.senha)

    def test_criar_professor(self):
        resposta = self.client.post(reverse('professores:criar'), {
            'nome': 'Maria Silva', 'matricula': 'PROF001', 'email': 'maria@escola.com',
            'telefone': '11999990000', 'carga_horaria': 20, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(Professor.objects.filter(matricula='PROF001').exists())

    def test_matricula_duplicada_nao_permite(self):
        Professor.objects.create(nome='Ana', matricula='PROF002', carga_horaria=10)
        resposta = self.client.post(reverse('professores:criar'), {
            'nome': 'Outra Pessoa', 'matricula': 'PROF002', 'carga_horaria': 5, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 200)  # form invalido, permanece na pagina
        self.assertEqual(Professor.objects.filter(matricula='PROF002').count(), 1)

    def test_alternar_ativo(self):
        professor = Professor.objects.create(nome='Carlos', matricula='PROF003', carga_horaria=15)
        self.client.post(reverse('professores:alternar_ativo', args=[professor.pk]))
        professor.refresh_from_db()
        self.assertFalse(professor.ativo)

    def test_criar_professor_com_etapas_e_turmas(self):
        turma_medio = Turma.objects.create(
            nome='1º Ano A', serie='1º Ano', turno=Turno.MATUTINO, etapa_ensino=EtapaEnsino.MEDIO,
        )
        turma_fund1 = Turma.objects.create(
            nome='3º Ano A', serie='3º Ano', turno=Turno.MATUTINO, etapa_ensino=EtapaEnsino.FUNDAMENTAL_1,
        )
        resposta = self.client.post(reverse('professores:criar'), {
            'nome': 'Daniela Rocha', 'matricula': 'PROF004', 'carga_horaria': 20, 'ativo': 'on',
            'etapas_autorizadas': [EtapaEnsino.MEDIO],
            'turmas_liberadas': [turma_fund1.pk],
        })
        self.assertEqual(resposta.status_code, 302, resposta.content)
        professor = Professor.objects.get(matricula='PROF004')
        self.assertEqual(professor.etapas_autorizadas, [EtapaEnsino.MEDIO])
        self.assertIn(turma_fund1, professor.turmas_liberadas.all())
        self.assertTrue(professor.pode_lecionar_em(turma_medio))
        self.assertTrue(professor.pode_lecionar_em(turma_fund1))


class ProfessorVinculoTurmaTests(TestCase):
    """Testa `Professor.pode_lecionar_em()` (Módulo 19: etapa + exceções)."""

    def setUp(self):
        self.turma_medio = Turma.objects.create(
            nome='1º Ano A', serie='1º Ano', turno=Turno.MATUTINO, etapa_ensino=EtapaEnsino.MEDIO,
        )
        self.turma_fund1 = Turma.objects.create(
            nome='3º Ano A', serie='3º Ano', turno=Turno.MATUTINO, etapa_ensino=EtapaEnsino.FUNDAMENTAL_1,
        )
        self.turma_fund2 = Turma.objects.create(
            nome='6º Ano A', serie='6º Ano', turno=Turno.MATUTINO, etapa_ensino=EtapaEnsino.FUNDAMENTAL_2,
        )

    def test_sem_etapas_autorizadas_nao_tem_restricao(self):
        professor = Professor.objects.create(nome='Sem restrição', matricula='VIN001', carga_horaria=20)
        self.assertTrue(professor.pode_lecionar_em(self.turma_medio))
        self.assertTrue(professor.pode_lecionar_em(self.turma_fund1))
        self.assertTrue(professor.pode_lecionar_em(self.turma_fund2))

    def test_etapa_autorizada_restringe_as_outras(self):
        professor = Professor.objects.create(
            nome='Só Médio', matricula='VIN002', carga_horaria=20, etapas_autorizadas=[EtapaEnsino.MEDIO],
        )
        self.assertTrue(professor.pode_lecionar_em(self.turma_medio))
        self.assertFalse(professor.pode_lecionar_em(self.turma_fund1))
        self.assertFalse(professor.pode_lecionar_em(self.turma_fund2))

    def test_fundamentais_nao_se_misturam(self):
        professor = Professor.objects.create(
            nome='Só Fund. I', matricula='VIN003', carga_horaria=20,
            etapas_autorizadas=[EtapaEnsino.FUNDAMENTAL_1],
        )
        self.assertTrue(professor.pode_lecionar_em(self.turma_fund1))
        self.assertFalse(professor.pode_lecionar_em(self.turma_fund2))

    def test_turma_liberada_e_excecao_a_etapa(self):
        professor = Professor.objects.create(
            nome='Coordenador', matricula='VIN004', carga_horaria=20, etapas_autorizadas=[EtapaEnsino.MEDIO],
        )
        professor.turmas_liberadas.add(self.turma_fund2)
        self.assertTrue(professor.pode_lecionar_em(self.turma_fund2))
        self.assertFalse(professor.pode_lecionar_em(self.turma_fund1))

    def test_turma_bloqueada_vence_mesmo_dentro_da_etapa(self):
        professor = Professor.objects.create(
            nome='Bloqueado numa turma', matricula='VIN005', carga_horaria=20,
            etapas_autorizadas=[EtapaEnsino.FUNDAMENTAL_2],
        )
        professor.turmas_bloqueadas.add(self.turma_fund2)
        self.assertFalse(professor.pode_lecionar_em(self.turma_fund2))

    def test_etapas_autorizadas_display(self):
        professor = Professor.objects.create(
            nome='Rótulos', matricula='VIN006', carga_horaria=20,
            etapas_autorizadas=[EtapaEnsino.FUNDAMENTAL_1, EtapaEnsino.MEDIO],
        )
        self.assertEqual(
            professor.etapas_autorizadas_display,
            [EtapaEnsino.FUNDAMENTAL_1.label, EtapaEnsino.MEDIO.label],
        )
