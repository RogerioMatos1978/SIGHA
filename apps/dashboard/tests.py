"""
Testes do módulo Dashboard: acesso exige login, indicadores de usuários
aparecem corretos, e cartões de módulos futuros aparecem como indisponíveis
em vez de zero (o que seria enganoso).
"""
from django.test import TestCase
from django.urls import reverse

from apps.usuarios.models import Usuario, Papel
from . import services


class ServicesTests(TestCase):
    def test_indicadores_usuarios(self):
        Usuario.objects.create_user(username='u1', password='SenhaForte123', papel=Papel.PROFESSOR)
        Usuario.objects.create_user(username='u2', password='SenhaForte123', papel=Papel.PROFESSOR, ativo=False)
        dados = services.obter_indicadores_usuarios()
        self.assertEqual(dados['total'], 2)
        self.assertEqual(dados['ativos'], 1)
        self.assertEqual(dados['inativos'], 1)

    def test_cartoes_modulos_futuros_ficam_indisponiveis(self):
        cartoes = services.obter_cartoes_resumo()
        por_chave = {c['chave']: c['valor'] for c in cartoes}
        self.assertIsNone(por_chave['professores'])
        self.assertIsNone(por_chave['conflitos'])


class DashboardViewTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.usuario = Usuario.objects.create_user(username='consulta1', password=self.senha, papel=Papel.CONSULTA)

    def test_exige_login(self):
        resposta = self.client.get(reverse('home'))
        self.assertEqual(resposta.status_code, 302)

    def test_usuario_autenticado_acessa_dashboard(self):
        self.client.login(username='consulta1', password=self.senha)
        resposta = self.client.get(reverse('home'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Usuários cadastrados')
