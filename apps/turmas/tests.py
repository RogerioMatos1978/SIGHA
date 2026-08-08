"""
Testes do módulo Turmas: permissões de acesso e CRUD básico.
"""
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.usuarios.models import Usuario, Papel
from .models import CursoTecnico, EtapaEnsino, Turma, Turno


class TurmaPermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.secretaria = Usuario.objects.create_user(username='sec3', password=self.senha, papel=Papel.SECRETARIA)
        self.professor = Usuario.objects.create_user(username='prof5', password=self.senha, papel=Papel.PROFESSOR)

    def test_secretaria_acessa_lista(self):
        self.client.login(username='sec3', password=self.senha)
        resposta = self.client.get(reverse('turmas:lista'))
        self.assertEqual(resposta.status_code, 200)

    def test_professor_nao_acessa_lista(self):
        self.client.login(username='prof5', password=self.senha)
        resposta = self.client.get(reverse('turmas:lista'))
        self.assertEqual(resposta.status_code, 403)

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('turmas:lista'))
        self.assertEqual(resposta.status_code, 302)


class TurmaCrudTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin5', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin5', password=self.senha)

    def test_criar_turma(self):
        resposta = self.client.post(reverse('turmas:criar'), {
            'nome': '1º Ano A', 'serie': '1º Ano', 'etapa_ensino': EtapaEnsino.FUNDAMENTAL_1,
            'turno': Turno.MATUTINO, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 302)
        turma = Turma.objects.get(nome='1º Ano A')
        self.assertEqual(turma.etapa_ensino, EtapaEnsino.FUNDAMENTAL_1)

    def test_mesma_turma_dois_turnos_e_permitido(self):
        Turma.objects.create(nome='1º Ano A', serie='1º Ano', turno=Turno.MATUTINO)
        resposta = self.client.post(reverse('turmas:criar'), {
            'nome': '1º Ano A', 'serie': '1º Ano', 'etapa_ensino': EtapaEnsino.FUNDAMENTAL_1,
            'turno': Turno.NOTURNO, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Turma.objects.filter(nome='1º Ano A').count(), 2)

    def test_mesmo_nome_e_turno_nao_permite_duplicar(self):
        Turma.objects.create(nome='2º Ano B', serie='2º Ano', turno=Turno.VESPERTINO)
        resposta = self.client.post(reverse('turmas:criar'), {
            'nome': '2º Ano B', 'serie': '2º Ano', 'etapa_ensino': EtapaEnsino.FUNDAMENTAL_1,
            'turno': Turno.VESPERTINO, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Turma.objects.filter(nome='2º Ano B').count(), 1)

    def test_alternar_ativo(self):
        turma = Turma.objects.create(nome='3º Ano C', serie='3º Ano', turno=Turno.INTEGRAL)
        self.client.post(reverse('turmas:alternar_ativo', args=[turma.pk]))
        turma.refresh_from_db()
        self.assertFalse(turma.ativo)


class TurmaEtapaEnsinoTests(TestCase):
    """
    Cobre o campo Etapa de Ensino (Fundamental I / II / Médio, divisão
    oficial do MEC/LDB) adicionado ao cadastro de Turma.
    """
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin_etapa', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin_etapa', password=self.senha)

    def test_turma_sem_etapa_explicita_usa_padrao(self):
        # Criada só via ORM (como o resto do sistema já faz há 6 módulos),
        # sem informar etapa_ensino — não pode quebrar por falta de default.
        turma = Turma.objects.create(nome='Turma sem etapa', serie='X', turno=Turno.MATUTINO)
        self.assertEqual(turma.etapa_ensino, EtapaEnsino.FUNDAMENTAL_2)

    def test_filtro_por_etapa_ensino(self):
        Turma.objects.create(
            nome='3º Ano A', serie='3º Ano', turno=Turno.MATUTINO, etapa_ensino=EtapaEnsino.FUNDAMENTAL_1,
        )
        Turma.objects.create(
            nome='1º Ano A (Médio)', serie='1º Ano', turno=Turno.MATUTINO, etapa_ensino=EtapaEnsino.MEDIO,
        )
        resposta = self.client.get(reverse('turmas:lista'), {'etapa_ensino': EtapaEnsino.FUNDAMENTAL_1})
        self.assertContains(resposta, '3º Ano A')
        self.assertNotContains(resposta, '1º Ano A (Médio)')

    def test_criar_turma_do_ensino_medio(self):
        resposta = self.client.post(reverse('turmas:criar'), {
            'nome': '2º Ano A', 'serie': '2º Ano', 'etapa_ensino': EtapaEnsino.MEDIO,
            'turno': Turno.MATUTINO, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 302)
        turma = Turma.objects.get(nome='2º Ano A')
        self.assertEqual(turma.etapa_ensino, EtapaEnsino.MEDIO)


class TurmaCursoTecnicoTests(TestCase):
    """
    Cobre o Curso Técnico (Módulo 20): catálogo de cursos do SENAI e o
    código do evento — a etapa de ensino "Curso Técnico" exige informar
    qual curso, as demais etapas não usam esse campo.
    """
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin_tecnico', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin_tecnico', password=self.senha)

    def test_curso_tecnico_sem_curso_e_invalido(self):
        turma = Turma(nome='Eletrotécnica A', serie='1º Módulo', turno=Turno.NOTURNO, etapa_ensino=EtapaEnsino.TECNICO)
        with self.assertRaises(ValidationError) as contexto:
            turma.full_clean()
        self.assertIn('curso_tecnico', contexto.exception.message_dict)

    def test_criar_turma_de_curso_tecnico_pela_tela(self):
        resposta = self.client.post(reverse('turmas:criar'), {
            'nome': 'Eletrotécnica A', 'serie': '1º Módulo', 'etapa_ensino': EtapaEnsino.TECNICO,
            'curso_tecnico': CursoTecnico.ELETROTECNICA, 'codigo_evento': '4321-2026',
            'turno': Turno.NOTURNO, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 302, resposta.context['form'].errors if resposta.status_code == 200 else '')
        turma = Turma.objects.get(nome='Eletrotécnica A')
        self.assertEqual(turma.curso_tecnico, CursoTecnico.ELETROTECNICA)
        self.assertEqual(turma.codigo_evento, '4321-2026')

    def test_outras_etapas_nao_exigem_curso_tecnico(self):
        turma = Turma(nome='6º Ano A', serie='6º Ano', turno=Turno.MATUTINO, etapa_ensino=EtapaEnsino.FUNDAMENTAL_2)
        turma.full_clean()  # não deve levantar ValidationError
