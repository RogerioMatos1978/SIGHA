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

    def test_cartao_professores_mostra_contagem_real(self):
        """Desde o Módulo 4, o app professores existe: o cartão deixa de ser None."""
        from apps.professores.models import Professor
        Professor.objects.create(nome='Ana', matricula='P1', carga_horaria=10)
        cartoes = services.obter_cartoes_resumo()
        por_chave = {c['chave']: c['valor'] for c in cartoes}
        self.assertEqual(por_chave['professores'], 1)

    def test_cartao_disciplinas_mostra_contagem_real(self):
        """Desde o Módulo 5, o app disciplinas existe: o cartão deixa de ser None."""
        from apps.disciplinas.models import Disciplina
        Disciplina.objects.create(nome='Matemática', sigla='MAT', quantidade_aulas_semana=5)
        cartoes = services.obter_cartoes_resumo()
        por_chave = {c['chave']: c['valor'] for c in cartoes}
        self.assertEqual(por_chave['disciplinas'], 1)

    def test_cartao_turmas_mostra_contagem_real(self):
        """Desde o Módulo 6, o app turmas existe: o cartão deixa de ser None."""
        from apps.turmas.models import Turma, Turno
        Turma.objects.create(nome='1º Ano A', serie='1º Ano', turno=Turno.MATUTINO)
        cartoes = services.obter_cartoes_resumo()
        por_chave = {c['chave']: c['valor'] for c in cartoes}
        self.assertEqual(por_chave['turmas'], 1)

    def test_cartoes_modulos_ainda_nao_implementados_ficam_indisponiveis(self):
        cartoes = services.obter_cartoes_resumo()
        por_chave = {c['chave']: c['valor'] for c in cartoes}
        self.assertIsNone(por_chave['ambientes'])
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
