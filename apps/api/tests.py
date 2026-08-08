"""
Testes da API (Módulo 15): autenticação/permissão por papel, CRUD de
cada recurso, reaproveitamento da validação de conflitos (Módulo 10) e
filtros por query string.
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


class ApiPermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.secretaria = Usuario.objects.create_user(username='sec15', password=self.senha, papel=Papel.SECRETARIA)
        self.professor_user = Usuario.objects.create_user(username='prof15', password=self.senha, papel=Papel.PROFESSOR)
        self.admin = Usuario.objects.create_user(username='admin15', password=self.senha, papel=Papel.ADMINISTRADOR)

    def test_anonimo_recebe_403(self):
        resposta = self.client.get(reverse('api:professor-list'))
        self.assertEqual(resposta.status_code, 403)

    def test_professor_sem_permissao_academica_recebe_403(self):
        self.client.login(username='prof15', password=self.senha)
        resposta = self.client.get(reverse('api:professor-list'))
        self.assertEqual(resposta.status_code, 403)

    def test_secretaria_acessa_professores(self):
        self.client.login(username='sec15', password=self.senha)
        resposta = self.client.get(reverse('api:professor-list'))
        self.assertEqual(resposta.status_code, 200)

    def test_usuarios_viewset_e_somente_leitura(self):
        self.client.login(username='admin15', password=self.senha)
        resposta = self.client.post(reverse('api:usuario-list'), {'username': 'novo', 'papel': Papel.PROFESSOR})
        self.assertEqual(resposta.status_code, 405)

    def test_professor_sem_permissao_de_usuarios_recebe_403_em_usuarios(self):
        self.client.login(username='sec15', password=self.senha)
        # secretaria gerencia acadêmico mas não usuários
        resposta = self.client.get(reverse('api:usuario-list'))
        self.assertEqual(resposta.status_code, 403)

    def test_admin_acessa_usuarios(self):
        self.client.login(username='admin15', password=self.senha)
        resposta = self.client.get(reverse('api:usuario-list'))
        self.assertEqual(resposta.status_code, 200)


class ApiCrudBaseTestCase(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin15b', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin15b', password=self.senha)


class ProfessorApiTests(ApiCrudBaseTestCase):
    def test_criar_professor(self):
        resposta = self.client.post(reverse('api:professor-list'), {
            'nome': 'Ana Souza', 'matricula': 'API001', 'carga_horaria': 20,
        })
        self.assertEqual(resposta.status_code, 201, resposta.content)
        self.assertTrue(Professor.objects.filter(matricula='API001').exists())

    def test_matricula_duplicada_retorna_400(self):
        Professor.objects.create(nome='Existente', matricula='API002', carga_horaria=10)
        resposta = self.client.post(reverse('api:professor-list'), {
            'nome': 'Outro', 'matricula': 'API002', 'carga_horaria': 10,
        })
        self.assertEqual(resposta.status_code, 400)

    def test_filtro_por_ativo(self):
        Professor.objects.create(nome='Ativo', matricula='API003', carga_horaria=10, ativo=True)
        Professor.objects.create(nome='Inativo', matricula='API004', carga_horaria=10, ativo=False)
        resposta = self.client.get(reverse('api:professor-list'), {'ativo': 'true'})
        nomes = [item['nome'] for item in resposta.json()]
        self.assertIn('Ativo', nomes)
        self.assertNotIn('Inativo', nomes)

    def test_etapas_autorizadas_aparece_na_resposta(self):
        professor = Professor.objects.create(
            nome='Com etapa', matricula='API005', carga_horaria=10, etapas_autorizadas=['MEDIO'],
        )
        resposta = self.client.get(reverse('api:professor-detail', args=[professor.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()['etapas_autorizadas'], ['MEDIO'])


class TurmaApiTests(ApiCrudBaseTestCase):
    def test_etapa_ensino_aparece_na_resposta(self):
        turma = Turma.objects.create(
            nome='6º Ano API', serie='6º Ano', turno=Turno.MATUTINO, etapa_ensino='FUNDAMENTAL_2',
        )
        resposta = self.client.get(reverse('api:turma-detail', args=[turma.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()['etapa_ensino'], 'FUNDAMENTAL_2')

    def test_filtro_por_etapa_ensino(self):
        Turma.objects.create(nome='3º Ano API', serie='3º Ano', turno=Turno.MATUTINO, etapa_ensino='FUNDAMENTAL_1')
        Turma.objects.create(nome='9º Ano API', serie='9º Ano', turno=Turno.MATUTINO, etapa_ensino='FUNDAMENTAL_2')
        resposta = self.client.get(reverse('api:turma-list'), {'etapa_ensino': 'FUNDAMENTAL_1'})
        nomes = [item['nome'] for item in resposta.json()]
        self.assertIn('3º Ano API', nomes)
        self.assertNotIn('9º Ano API', nomes)


class HorarioApiTests(ApiCrudBaseTestCase):
    def test_fim_antes_do_inicio_retorna_400(self):
        resposta = self.client.post(reverse('api:horario-list'), {
            'ordem': 1, 'inicio': '08:00:00', 'fim': '07:00:00',
        })
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('fim', resposta.json())

    def test_criar_horario_valido(self):
        resposta = self.client.post(reverse('api:horario-list'), {
            'ordem': 1, 'inicio': '07:00:00', 'fim': '07:50:00',
        })
        self.assertEqual(resposta.status_code, 201)


class GradeAulaApiTests(ApiCrudBaseTestCase):
    def setUp(self):
        super().setUp()
        self.turma = Turma.objects.create(nome='1º Ano A', serie='1º Ano', turno=Turno.MATUTINO)
        self.turma_b = Turma.objects.create(nome='1º Ano B', serie='1º Ano', turno=Turno.MATUTINO)
        self.disciplina = Disciplina.objects.create(nome='Matemática', sigla='MAT', quantidade_aulas_semana=5)
        self.professor = Professor.objects.create(nome='Ana', matricula='API010', carga_horaria=20)
        self.ambiente = Ambiente.objects.create(nome='Sala Api', tipo=TipoAmbiente.SALA, capacidade=1)
        self.horario = Horario.objects.create(ordem=1, inicio=datetime.time(7, 0), fim=datetime.time(7, 50))

    def _payload(self, **overrides):
        dados = dict(
            turma=self.turma.pk, disciplina=self.disciplina.pk, professor=self.professor.pk,
            ambiente=self.ambiente.pk, dia_semana=DiaSemana.SEGUNDA, horario=self.horario.pk,
            ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        dados.update(overrides)
        return dados

    def test_criar_aula_valida_seta_criado_por(self):
        resposta = self.client.post(reverse('api:gradeaula-list'), self._payload())
        self.assertEqual(resposta.status_code, 201, resposta.content)
        aula = GradeAula.objects.get(pk=resposta.json()['id'])
        self.assertEqual(aula.criado_por, self.admin)

    def test_professor_em_duas_turmas_ao_mesmo_tempo_retorna_400(self):
        # Este conflito também é uma UniqueConstraint do modelo (Módulo 10), então
        # o DRF já barra na validação automática de unicidade, antes mesmo de
        # chegar ao full_clean() customizado — daí o erro vir em non_field_errors.
        self.client.post(reverse('api:gradeaula-list'), self._payload())
        resposta = self.client.post(reverse('api:gradeaula-list'), self._payload(
            turma=self.turma_b.pk, ambiente=Ambiente.objects.create(nome='Sala Api 2', tipo=TipoAmbiente.SALA).pk,
        ))
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('non_field_errors', resposta.json())

    def test_professor_indisponivel_retorna_erro_no_campo_professor(self):
        # Esta regra NÃO é uma UniqueConstraint — só o full_clean() (Módulo 10)
        # a conhece, então precisa mesmo passar pelo FullCleanMixin da API.
        from apps.disponibilidade.models import DisponibilidadeProfessor
        DisponibilidadeProfessor.objects.create(
            professor=self.professor, dia_semana=DiaSemana.SEGUNDA, horario=self.horario, disponivel=False,
        )
        resposta = self.client.post(reverse('api:gradeaula-list'), self._payload())
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('professor', resposta.json())

    def test_filtro_por_turma(self):
        self.client.post(reverse('api:gradeaula-list'), self._payload())
        resposta = self.client.get(reverse('api:gradeaula-list'), {'turma': self.turma.pk})
        self.assertEqual(len(resposta.json()), 1)
        resposta_outra = self.client.get(reverse('api:gradeaula-list'), {'turma': self.turma_b.pk})
        self.assertEqual(len(resposta_outra.json()), 0)


class AtribuicaoApiTests(ApiCrudBaseTestCase):
    def test_professor_fora_do_vinculo_aparece_como_aviso_sem_bloquear(self):
        turma = Turma.objects.create(nome='1º Ano Medio API', serie='1º Ano', turno=Turno.MATUTINO, etapa_ensino='MEDIO')
        disciplina = Disciplina.objects.create(nome='Física', sigla='FISAPI', quantidade_aulas_semana=2)
        professor = Professor.objects.create(
            nome='Só Fundamental', matricula='API021', carga_horaria=20, etapas_autorizadas=['FUNDAMENTAL_1'],
        )
        resposta = self.client.post(reverse('api:atribuicao-list'), {
            'turma': turma.pk, 'disciplina': disciplina.pk, 'professor': professor.pk,
        })
        self.assertEqual(resposta.status_code, 201, resposta.content)
        self.assertTrue(resposta.json()['professor_fora_do_vinculo'])

    def test_atribuicao_duplicada_para_mesma_turma_disciplina_retorna_400(self):
        turma = Turma.objects.create(nome='2º Ano A', serie='2º Ano', turno=Turno.VESPERTINO)
        disciplina = Disciplina.objects.create(nome='Português', sigla='POR', quantidade_aulas_semana=3)
        professor = Professor.objects.create(nome='Bruno', matricula='API020', carga_horaria=20)
        Atribuicao.objects.create(turma=turma, disciplina=disciplina, professor=professor)

        resposta = self.client.post(reverse('api:atribuicao-list'), {
            'turma': turma.pk, 'disciplina': disciplina.pk, 'professor': professor.pk,
        })
        self.assertEqual(resposta.status_code, 400)


class SubstituicaoApiTests(ApiCrudBaseTestCase):
    def setUp(self):
        super().setUp()
        self.turma = Turma.objects.create(nome='2º Ano API Sub', serie='2º Ano', turno=Turno.MATUTINO)
        disciplina = Disciplina.objects.create(nome='Química', sigla='QUIAPI', quantidade_aulas_semana=2)
        self.titular = Professor.objects.create(nome='Titular API', matricula='API030', carga_horaria=20)
        self.substituto = Professor.objects.create(nome='Substituto API', matricula='API031', carga_horaria=20)
        horario = Horario.objects.create(ordem=1, inicio=datetime.time(7, 0), fim=datetime.time(7, 50))
        self.aula = GradeAula.objects.create(
            turma=self.turma, disciplina=disciplina, professor=self.titular,
            ambiente=Ambiente.objects.create(nome='Sala Sub API', tipo=TipoAmbiente.SALA),
            dia_semana=DiaSemana.SEGUNDA, horario=horario, ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )

    def test_criar_substituicao_valida(self):
        resposta = self.client.post(reverse('api:substituicao-list'), {
            'aula': self.aula.pk, 'data': '2026-08-10', 'professor_substituto': self.substituto.pk,
        })
        self.assertEqual(resposta.status_code, 201, resposta.content)

    def test_data_fora_do_dia_da_semana_retorna_400(self):
        resposta = self.client.post(reverse('api:substituicao-list'), {
            'aula': self.aula.pk, 'data': '2026-08-11', 'professor_substituto': self.substituto.pk,
        })
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('data', resposta.json())
