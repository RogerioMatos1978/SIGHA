"""
Testes do módulo Auditoria: permissões (só Administrador), captura de
criação/atualização/remoção via sinais, login/logout/falha de login, e
os filtros da tela de consulta.
"""
from django.test import TestCase
from django.urls import reverse

from apps.professores.models import Professor
from apps.usuarios.models import Papel, Usuario

from .models import Acao, RegistroAuditoria


class AuditoriaPermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.coordenador = Usuario.objects.create_user(username='coord16', password=self.senha, papel=Papel.COORDENADOR)
        self.secretaria = Usuario.objects.create_user(username='sec16', password=self.senha, papel=Papel.SECRETARIA)
        self.admin = Usuario.objects.create_user(username='admin16', password=self.senha, papel=Papel.ADMINISTRADOR)

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('auditoria:lista'))
        self.assertEqual(resposta.status_code, 302)

    def test_coordenador_nao_acessa(self):
        # Coordenador gerencia usuários e acadêmico, mas Auditoria é só Administrador.
        self.client.login(username='coord16', password=self.senha)
        resposta = self.client.get(reverse('auditoria:lista'))
        self.assertEqual(resposta.status_code, 403)

    def test_secretaria_nao_acessa(self):
        self.client.login(username='sec16', password=self.senha)
        resposta = self.client.get(reverse('auditoria:lista'))
        self.assertEqual(resposta.status_code, 403)

    def test_administrador_acessa(self):
        self.client.login(username='admin16', password=self.senha)
        resposta = self.client.get(reverse('auditoria:lista'))
        self.assertEqual(resposta.status_code, 200)


class SinaisDeModeloTests(TestCase):
    def test_criar_professor_gera_registro_de_criacao(self):
        RegistroAuditoria.objects.all().delete()
        Professor.objects.create(nome='Ana', matricula='AUD001', carga_horaria=20)
        registro = RegistroAuditoria.objects.get(modelo='Professor', objeto_id__isnull=False, acao=Acao.CRIACAO)
        self.assertIn('Ana', registro.objeto_repr)
        self.assertIsNone(registro.usuario)  # criado direto via ORM, sem request

    def test_atualizar_professor_gera_registro_de_atualizacao(self):
        professor = Professor.objects.create(nome='Bruno', matricula='AUD002', carga_horaria=10)
        RegistroAuditoria.objects.all().delete()
        professor.carga_horaria = 15
        professor.save()
        self.assertTrue(RegistroAuditoria.objects.filter(modelo='Professor', acao=Acao.ATUALIZACAO).exists())

    def test_remover_professor_gera_registro_de_remocao(self):
        professor = Professor.objects.create(nome='Carla', matricula='AUD003', carga_horaria=10)
        professor_id = professor.pk
        RegistroAuditoria.objects.all().delete()
        professor.delete()
        registro = RegistroAuditoria.objects.get(modelo='Professor', acao=Acao.REMOCAO)
        self.assertEqual(registro.objeto_id, str(professor_id))

    def test_registro_de_auditoria_nao_audita_a_si_mesmo(self):
        contagem_antes = RegistroAuditoria.objects.count()
        RegistroAuditoria.objects.create(acao=Acao.CRIACAO, modelo='Teste', objeto_id='1', objeto_repr='teste')
        # só o registro criado manualmente + nada a mais (nenhum "eco")
        self.assertEqual(RegistroAuditoria.objects.count(), contagem_antes + 1)

    def test_criar_professor_via_view_registra_usuario_autenticado(self):
        senha = 'SenhaForte123'
        admin = Usuario.objects.create_user(username='admin16b', password=senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin16b', password=senha)
        RegistroAuditoria.objects.all().delete()
        self.client.post(reverse('professores:criar'), {
            'nome': 'Diego', 'matricula': 'AUD004', 'carga_horaria': 12, 'ativo': 'on',
        })
        registro = RegistroAuditoria.objects.get(modelo='Professor', acao=Acao.CRIACAO)
        self.assertEqual(registro.usuario, admin)


class SinaisDeLoginTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.usuario = Usuario.objects.create_user(username='login16', password=self.senha, papel=Papel.SECRETARIA)

    def test_login_bem_sucedido_gera_registro(self):
        RegistroAuditoria.objects.all().delete()
        self.client.post(reverse('usuarios:login'), {'username': 'login16', 'password': self.senha})
        self.assertTrue(RegistroAuditoria.objects.filter(acao=Acao.LOGIN, usuario=self.usuario).exists())

    def test_login_com_senha_errada_gera_registro_de_falha(self):
        RegistroAuditoria.objects.all().delete()
        self.client.post(reverse('usuarios:login'), {'username': 'login16', 'password': 'senhaerrada'})
        registro = RegistroAuditoria.objects.get(acao=Acao.LOGIN_FALHOU)
        self.assertIsNone(registro.usuario)
        self.assertEqual(registro.objeto_repr, 'login16')

    def test_logout_gera_registro(self):
        self.client.login(username='login16', password=self.senha)
        RegistroAuditoria.objects.all().delete()
        self.client.post(reverse('usuarios:logout'))
        self.assertTrue(RegistroAuditoria.objects.filter(acao=Acao.LOGOUT, usuario=self.usuario).exists())


class ConsultaViewTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin16c', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin16c', password=self.senha)
        RegistroAuditoria.objects.all().delete()
        Professor.objects.create(nome='Emilia', matricula='AUD005', carga_horaria=10)

    def test_lista_mostra_registro(self):
        resposta = self.client.get(reverse('auditoria:lista'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Professor')

    def test_filtro_por_modelo(self):
        resposta = self.client.get(reverse('auditoria:lista'), {'modelo': 'Professor'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Emilia')

    def test_filtro_por_modelo_sem_correspondencia(self):
        resposta = self.client.get(reverse('auditoria:lista'), {'modelo': 'Turma'})
        self.assertNotContains(resposta, 'Emilia')
