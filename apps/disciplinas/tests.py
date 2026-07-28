"""
Testes do módulo Disciplinas: permissões de acesso e CRUD básico.
"""
from django.test import TestCase
from django.urls import reverse

from apps.ambientes.models import TipoAmbiente
from apps.usuarios.models import Usuario, Papel
from .models import Disciplina


class DisciplinaPermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.secretaria = Usuario.objects.create_user(username='sec2', password=self.senha, papel=Papel.SECRETARIA)
        self.professor = Usuario.objects.create_user(username='prof4', password=self.senha, papel=Papel.PROFESSOR)

    def test_secretaria_acessa_lista(self):
        self.client.login(username='sec2', password=self.senha)
        resposta = self.client.get(reverse('disciplinas:lista'))
        self.assertEqual(resposta.status_code, 200)

    def test_professor_nao_acessa_lista(self):
        self.client.login(username='prof4', password=self.senha)
        resposta = self.client.get(reverse('disciplinas:lista'))
        self.assertEqual(resposta.status_code, 403)

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('disciplinas:lista'))
        self.assertEqual(resposta.status_code, 302)


class DisciplinaCrudTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin4', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin4', password=self.senha)

    def test_criar_disciplina(self):
        resposta = self.client.post(reverse('disciplinas:criar'), {
            'nome': 'Matemática', 'sigla': 'mat', 'quantidade_aulas_semana': 5, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 302)
        disciplina = Disciplina.objects.get(nome='Matemática')
        self.assertEqual(disciplina.sigla, 'MAT')  # normalizado para maiuscula

    def test_sigla_duplicada_nao_permite(self):
        Disciplina.objects.create(nome='História', sigla='HIST', quantidade_aulas_semana=3)
        resposta = self.client.post(reverse('disciplinas:criar'), {
            'nome': 'Outra', 'sigla': 'HIST', 'quantidade_aulas_semana': 2, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Disciplina.objects.filter(sigla='HIST').count(), 1)

    def test_alternar_ativo(self):
        disciplina = Disciplina.objects.create(nome='Física', sigla='FIS', quantidade_aulas_semana=4)
        self.client.post(reverse('disciplinas:alternar_ativo', args=[disciplina.pk]))
        disciplina.refresh_from_db()
        self.assertFalse(disciplina.ativo)

    def test_tipo_ambiente_e_opcional(self):
        disciplina = Disciplina.objects.create(nome='Português', sigla='POR', quantidade_aulas_semana=4)
        self.assertIsNone(disciplina.tipo_ambiente)

    def test_criar_disciplina_com_tipo_ambiente_especifico(self):
        resposta = self.client.post(reverse('disciplinas:criar'), {
            'nome': 'Educação Física', 'sigla': 'EDF', 'quantidade_aulas_semana': 2,
            'tipo_ambiente': TipoAmbiente.QUADRA, 'ativo': 'on',
        })
        self.assertEqual(resposta.status_code, 302)
        disciplina = Disciplina.objects.get(sigla='EDF')
        self.assertEqual(disciplina.tipo_ambiente, TipoAmbiente.QUADRA)
