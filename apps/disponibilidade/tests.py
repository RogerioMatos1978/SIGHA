"""
Testes do módulo Disponibilidade: permissões, geração automática da grade
e atualização via POST.
"""
import datetime

from django.test import TestCase
from django.urls import reverse

from apps.usuarios.models import Usuario, Papel
from apps.professores.models import Professor
from apps.horarios.models import Horario
from .models import DisponibilidadeProfessor, DiaSemana


class DisponibilidadePermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.secretaria = Usuario.objects.create_user(username='sec6', password=self.senha, papel=Papel.SECRETARIA)
        self.professor_user = Usuario.objects.create_user(username='prof8', password=self.senha, papel=Papel.PROFESSOR)

    def test_secretaria_acessa_lista(self):
        self.client.login(username='sec6', password=self.senha)
        resposta = self.client.get(reverse('disponibilidade:lista'))
        self.assertEqual(resposta.status_code, 200)

    def test_professor_nao_acessa_lista(self):
        self.client.login(username='prof8', password=self.senha)
        resposta = self.client.get(reverse('disponibilidade:lista'))
        self.assertEqual(resposta.status_code, 403)

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('disponibilidade:lista'))
        self.assertEqual(resposta.status_code, 302)


class DisponibilidadeGradeTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin8', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin8', password=self.senha)
        self.professor = Professor.objects.create(nome='Carla Dias', matricula='PROF999', carga_horaria=20)
        self.h1 = Horario.objects.create(ordem=1, inicio=datetime.time(7, 0), fim=datetime.time(7, 50))
        self.h2 = Horario.objects.create(ordem=2, inicio=datetime.time(7, 50), fim=datetime.time(8, 40))
        self.intervalo = Horario.objects.create(ordem=3, inicio=datetime.time(8, 40), fim=datetime.time(9, 0), intervalo=True)

    def test_visitar_grade_cria_registros_disponiveis_por_padrao(self):
        resposta = self.client.get(reverse('disponibilidade:editar', args=[self.professor.pk]))
        self.assertEqual(resposta.status_code, 200)
        # 2 horarios de aula (o intervalo fica de fora) x 5 dias = 10 registros
        total = DisponibilidadeProfessor.objects.filter(professor=self.professor).count()
        self.assertEqual(total, 10)
        self.assertTrue(all(
            DisponibilidadeProfessor.objects.filter(professor=self.professor).values_list('disponivel', flat=True)
        ))

    def test_intervalo_nao_entra_na_grade(self):
        self.client.get(reverse('disponibilidade:editar', args=[self.professor.pk]))
        existe_para_intervalo = DisponibilidadeProfessor.objects.filter(
            professor=self.professor, horario=self.intervalo
        ).exists()
        self.assertFalse(existe_para_intervalo)

    def test_desmarcar_horario_marca_como_indisponivel(self):
        self.client.get(reverse('disponibilidade:editar', args=[self.professor.pk]))
        # marca disponível só na segunda-feira, horário 1 (todos os outros ficam desmarcados)
        campos = {f'disp_{self.h1.id}_{DiaSemana.SEGUNDA}': 'on'}
        self.client.post(reverse('disponibilidade:editar', args=[self.professor.pk]), campos)

        disponiveis = DisponibilidadeProfessor.objects.filter(professor=self.professor, disponivel=True)
        self.assertEqual(disponiveis.count(), 1)
        self.assertEqual(disponiveis.first().horario, self.h1)
        self.assertEqual(disponiveis.first().dia_semana, DiaSemana.SEGUNDA)
