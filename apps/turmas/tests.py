"""
Testes do módulo Turmas: permissões de acesso e CRUD básico.
"""
from django.test import TestCase
from django.urls import reverse

from apps.usuarios.models import Usuario, Papel
from .models import Turma, Turno


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
            'nome': '1º Ano A', 'serie': '1º Ano', 'turno': Turno.MATUTINO, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(Turma.objects.filter(nome='1º Ano A').exists())

    def test_mesma_turma_dois_turnos_e_permitido(self):
        Turma.objects.create(nome='1º Ano A', serie='1º Ano', turno=Turno.MATUTINO)
        resposta = self.client.post(reverse('turmas:criar'), {
            'nome': '1º Ano A', 'serie': '1º Ano', 'turno': Turno.NOTURNO, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Turma.objects.filter(nome='1º Ano A').count(), 2)

    def test_mesmo_nome_e_turno_nao_permite_duplicar(self):
        Turma.objects.create(nome='2º Ano B', serie='2º Ano', turno=Turno.VESPERTINO)
        resposta = self.client.post(reverse('turmas:criar'), {
            'nome': '2º Ano B', 'serie': '2º Ano', 'turno': Turno.VESPERTINO, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Turma.objects.filter(nome='2º Ano B').count(), 1)

    def test_alternar_ativo(self):
        turma = Turma.objects.create(nome='3º Ano C', serie='3º Ano', turno=Turno.INTEGRAL)
        self.client.post(reverse('turmas:alternar_ativo', args=[turma.pk]))
        turma.refresh_from_db()
        self.assertFalse(turma.ativo)
