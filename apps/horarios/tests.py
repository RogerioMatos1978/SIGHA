"""
Testes do módulo Horários: permissões, CRUD e a regra de fim > início.
"""
import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.usuarios.models import Usuario, Papel
from .models import Horario


class HorarioModelTests(TestCase):
    def test_fim_antes_do_inicio_e_invalido(self):
        horario = Horario(ordem=1, inicio=datetime.time(8, 0), fim=datetime.time(7, 0))
        with self.assertRaises(ValidationError):
            horario.full_clean()

    def test_horario_valido_passa_na_validacao(self):
        horario = Horario(ordem=1, inicio=datetime.time(7, 0), fim=datetime.time(7, 50))
        horario.full_clean()  # não deve levantar exceção


class HorarioPermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.secretaria = Usuario.objects.create_user(username='sec5', password=self.senha, papel=Papel.SECRETARIA)
        self.professor = Usuario.objects.create_user(username='prof7', password=self.senha, papel=Papel.PROFESSOR)

    def test_secretaria_acessa_lista(self):
        self.client.login(username='sec5', password=self.senha)
        resposta = self.client.get(reverse('horarios:lista'))
        self.assertEqual(resposta.status_code, 200)

    def test_professor_nao_acessa_lista(self):
        self.client.login(username='prof7', password=self.senha)
        resposta = self.client.get(reverse('horarios:lista'))
        self.assertEqual(resposta.status_code, 403)

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('horarios:lista'))
        self.assertEqual(resposta.status_code, 302)


class HorarioCrudTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin7', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin7', password=self.senha)

    def test_criar_horario(self):
        resposta = self.client.post(reverse('horarios:criar'), {
            'ordem': 1, 'inicio': '07:00', 'fim': '07:50', 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(Horario.objects.filter(ordem=1).exists())

    def test_ordem_duplicada_nao_permite(self):
        Horario.objects.create(ordem=1, inicio=datetime.time(7, 0), fim=datetime.time(7, 50))
        resposta = self.client.post(reverse('horarios:criar'), {
            'ordem': 1, 'inicio': '08:40', 'fim': '09:30', 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Horario.objects.filter(ordem=1).count(), 1)

    def test_fim_antes_do_inicio_via_formulario(self):
        resposta = self.client.post(reverse('horarios:criar'), {
            'ordem': 2, 'inicio': '10:00', 'fim': '09:00', 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Horario.objects.filter(ordem=2).exists())

    def test_alternar_ativo(self):
        horario = Horario.objects.create(ordem=3, inicio=datetime.time(9, 50), fim=datetime.time(10, 40))
        self.client.post(reverse('horarios:alternar_ativo', args=[horario.pk]))
        horario.refresh_from_db()
        self.assertFalse(horario.ativo)
