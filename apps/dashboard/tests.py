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

    def test_cartao_ambientes_mostra_contagem_real(self):
        """Desde o Módulo 7, o app ambientes existe: o cartão deixa de ser None."""
        from apps.ambientes.models import Ambiente, TipoAmbiente
        Ambiente.objects.create(nome='Biblioteca', tipo=TipoAmbiente.BIBLIOTECA, capacidade=1)
        cartoes = services.obter_cartoes_resumo()
        por_chave = {c['chave']: c['valor'] for c in cartoes}
        self.assertEqual(por_chave['ambientes'], 1)

    def test_cartao_conflitos_mostra_zero_desde_o_modulo_grade(self):
        """
        Desde o Módulo 10 (Grade), este cartão deixa de ser "Em breve": as
        regras de conflito impedem qualquer aula conflitante de ser salva,
        então "0 conflitos" é sempre um valor real, não um placeholder.
        """
        cartoes = services.obter_cartoes_resumo()
        por_chave = {c['chave']: c['valor'] for c in cartoes}
        self.assertEqual(por_chave['conflitos'], 0)

    def test_cartao_carga_horaria_conta_aulas_da_grade_no_ano_atual(self):
        from django.utils import timezone

        from apps.disponibilidade.models import DiaSemana
        from apps.grade.models import GradeAula, Semestre
        from apps.horarios.models import Horario
        from apps.professores.models import Professor
        from apps.turmas.models import Turma, Turno
        from apps.ambientes.models import Ambiente, TipoAmbiente
        from apps.disciplinas.models import Disciplina
        import datetime

        turma = Turma.objects.create(nome='2º Ano A', serie='2º Ano', turno=Turno.MATUTINO)
        disciplina = Disciplina.objects.create(nome='Português', sigla='POR', quantidade_aulas_semana=5)
        professor = Professor.objects.create(nome='Ana', matricula='PGRADE1', carga_horaria=20)
        ambiente = Ambiente.objects.create(nome='Sala Dashboard', tipo=TipoAmbiente.SALA, capacidade=1)
        horario = Horario.objects.create(ordem=1, inicio=datetime.time(7, 0), fim=datetime.time(7, 50))
        GradeAula.objects.create(
            turma=turma, disciplina=disciplina, professor=professor, ambiente=ambiente,
            dia_semana=DiaSemana.SEGUNDA, horario=horario,
            ano_letivo=timezone.now().year, semestre=Semestre.PRIMEIRO,
        )
        cartoes = services.obter_cartoes_resumo()
        por_chave = {c['chave']: c['valor'] for c in cartoes}
        self.assertEqual(por_chave['carga_horaria'], 1)


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
