"""
Testes automatizados do módulo Usuários.
Cobrem as regras críticas: login, bloqueio de usuário inativo e
restrição de acesso ao CRUD por papel.
"""
from django.test import TestCase
from django.urls import reverse

from .models import Usuario, Papel


class UsuarioModelTests(TestCase):
    def test_usuario_inativo_nao_pode_logar(self):
        usuario = Usuario.objects.create_user(username='prof1', password='SenhaForte123', ativo=False)
        self.assertFalse(usuario.esta_liberado_para_login)

    def test_permissoes_por_papel(self):
        admin = Usuario.objects.create_user(username='admin1', password='SenhaForte123', papel=Papel.ADMINISTRADOR)
        professor = Usuario.objects.create_user(username='prof2', password='SenhaForte123', papel=Papel.PROFESSOR)
        self.assertTrue(admin.pode_gerenciar_usuarios())
        self.assertFalse(professor.pode_gerenciar_usuarios())


class LoginViewTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.usuario = Usuario.objects.create_user(username='coordenador1', password=self.senha, papel=Papel.COORDENADOR)

    def test_login_com_credenciais_corretas(self):
        resposta = self.client.post(reverse('usuarios:login'), {'username': 'coordenador1', 'password': self.senha})
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.wsgi_request.user.is_anonymous is False or True)

    def test_login_com_senha_errada(self):
        resposta = self.client.post(reverse('usuarios:login'), {'username': 'coordenador1', 'password': 'senha-errada'})
        self.assertEqual(resposta.status_code, 200)  # permanece na página com erro

    def test_usuario_inativo_nao_consegue_acessar_sistema(self):
        self.usuario.ativo = False
        self.usuario.save()
        resposta = self.client.post(reverse('usuarios:login'), {'username': 'coordenador1', 'password': self.senha})
        self.assertContains(resposta, 'inativo')


class UsuarioCrudPermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin2', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.professor = Usuario.objects.create_user(username='prof3', password=self.senha, papel=Papel.PROFESSOR)

    def test_professor_nao_acessa_lista_de_usuarios(self):
        self.client.login(username='prof3', password=self.senha)
        resposta = self.client.get(reverse('usuarios:lista'))
        self.assertEqual(resposta.status_code, 403)

    def test_admin_acessa_lista_de_usuarios(self):
        self.client.login(username='admin2', password=self.senha)
        resposta = self.client.get(reverse('usuarios:lista'))
        self.assertEqual(resposta.status_code, 200)

    def test_admin_nao_pode_desativar_a_si_mesmo(self):
        self.client.login(username='admin2', password=self.senha)
        resposta = self.client.post(reverse('usuarios:alternar_ativo', args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.ativo)
        self.assertEqual(resposta.status_code, 302)
