"""
Testes do módulo Professores: permissões de acesso e CRUD básico.
"""
from django.test import TestCase
from django.urls import reverse

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
