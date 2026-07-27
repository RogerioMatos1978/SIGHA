"""
Testes do módulo Ambientes: permissões de acesso e CRUD básico.
"""
from django.test import TestCase
from django.urls import reverse

from apps.usuarios.models import Usuario, Papel
from .models import Ambiente, TipoAmbiente


class AmbientePermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.secretaria = Usuario.objects.create_user(username='sec4', password=self.senha, papel=Papel.SECRETARIA)
        self.professor = Usuario.objects.create_user(username='prof6', password=self.senha, papel=Papel.PROFESSOR)

    def test_secretaria_acessa_lista(self):
        self.client.login(username='sec4', password=self.senha)
        resposta = self.client.get(reverse('ambientes:lista'))
        self.assertEqual(resposta.status_code, 200)

    def test_professor_nao_acessa_lista(self):
        self.client.login(username='prof6', password=self.senha)
        resposta = self.client.get(reverse('ambientes:lista'))
        self.assertEqual(resposta.status_code, 403)

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('ambientes:lista'))
        self.assertEqual(resposta.status_code, 302)


class AmbienteCrudTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin6', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin6', password=self.senha)

    def test_criar_ambiente(self):
        resposta = self.client.post(reverse('ambientes:criar'), {
            'nome': 'Laboratório de Informática', 'tipo': TipoAmbiente.LABORATORIO, 'capacidade': 1, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(Ambiente.objects.filter(nome='Laboratório de Informática').exists())

    def test_nome_duplicado_nao_permite(self):
        Ambiente.objects.create(nome='Biblioteca', tipo=TipoAmbiente.BIBLIOTECA, capacidade=1)
        resposta = self.client.post(reverse('ambientes:criar'), {
            'nome': 'Biblioteca', 'tipo': TipoAmbiente.BIBLIOTECA, 'capacidade': 1, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Ambiente.objects.filter(nome='Biblioteca').count(), 1)

    def test_alternar_ativo(self):
        ambiente = Ambiente.objects.create(nome='Quadra Poliesportiva', tipo=TipoAmbiente.QUADRA, capacidade=1)
        self.client.post(reverse('ambientes:alternar_ativo', args=[ambiente.pk]))
        ambiente.refresh_from_db()
        self.assertFalse(ambiente.ativo)
