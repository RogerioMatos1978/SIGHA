"""
Testes do módulo Backup: permissões (só Administrador), geração e
restauração reais via pg_dump/psql (contra o próprio banco de teste),
remoção, limpeza por retenção, e a integração com a Auditoria (Módulo 16).
"""
from datetime import timedelta

from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from apps.auditoria.models import Acao, RegistroAuditoria
from apps.professores.models import Professor
from apps.usuarios.models import Papel, Usuario

from . import services
from .models import RegistroBackup


class BackupPermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.coordenador = Usuario.objects.create_user(username='coord17', password=self.senha, papel=Papel.COORDENADOR)
        self.secretaria = Usuario.objects.create_user(username='sec17', password=self.senha, papel=Papel.SECRETARIA)
        self.admin = Usuario.objects.create_user(username='admin17', password=self.senha, papel=Papel.ADMINISTRADOR)

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('backup:lista'))
        self.assertEqual(resposta.status_code, 302)

    def test_coordenador_nao_acessa(self):
        self.client.login(username='coord17', password=self.senha)
        resposta = self.client.get(reverse('backup:lista'))
        self.assertEqual(resposta.status_code, 403)

    def test_secretaria_nao_acessa(self):
        self.client.login(username='sec17', password=self.senha)
        resposta = self.client.get(reverse('backup:lista'))
        self.assertEqual(resposta.status_code, 403)

    def test_administrador_acessa(self):
        self.client.login(username='admin17', password=self.senha)
        resposta = self.client.get(reverse('backup:lista'))
        self.assertEqual(resposta.status_code, 200)


class GerarBackupServiceTests(TestCase):
    def test_gerar_backup_cria_arquivo_e_registro(self):
        registro = services.gerar_backup(usuario=None)
        self.assertTrue(registro.existe_no_disco())
        self.assertGreater(registro.tamanho_bytes, 0)
        self.assertTrue(registro.nome_arquivo.startswith('sigha_'))
        conteudo = registro.caminho_arquivo().read_text(encoding='utf-8', errors='ignore')
        self.assertIn('professores_professor', conteudo)

    def test_gerar_backup_registra_usuario_quando_autenticado(self):
        admin = Usuario.objects.create_user(username='gerabkp1', password='SenhaForte123', papel=Papel.ADMINISTRADOR)
        registro = services.gerar_backup(usuario=admin)
        self.assertEqual(registro.criado_por, admin)

    def test_gerar_backup_cria_entrada_de_auditoria_de_criacao(self):
        RegistroAuditoria.objects.all().delete()
        registro = services.gerar_backup(usuario=None)
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                modelo='RegistroBackup', acao=Acao.CRIACAO, objeto_id=str(registro.pk),
            ).exists()
        )


class RestaurarBackupServiceTests(TransactionTestCase):
    """
    TransactionTestCase (não TestCase): restaurar roda `psql` num processo
    externo, que precisa de lock exclusivo nas tabelas para os DROP/CREATE
    do dump. Dentro de um TestCase comum, o próprio teste já está dentro
    de uma transação aberta segurando essas tabelas — e o psql ficaria
    esperando esse lock para sempre. TransactionTestCase não embrulha o
    teste numa transação (ele limpa as tabelas por TRUNCATE ao final),
    então não há conflito de lock com o processo externo.
    """
    def test_restaurar_traz_de_volta_registro_apagado(self):
        Professor.objects.create(nome='Fabio Backup', matricula='BKP001', carga_horaria=10)
        registro = services.gerar_backup(usuario=None)

        Professor.objects.filter(matricula='BKP001').delete()
        self.assertFalse(Professor.objects.filter(matricula='BKP001').exists())

        services.restaurar_backup(registro, usuario=None)
        self.assertTrue(Professor.objects.filter(matricula='BKP001').exists())

    def test_restaurar_gera_entrada_de_auditoria_com_acao_restauracao(self):
        registro = services.gerar_backup(usuario=None)
        RegistroAuditoria.objects.all().delete()
        services.restaurar_backup(registro, usuario=None)
        self.assertTrue(
            RegistroAuditoria.objects.filter(modelo='RegistroBackup', acao=Acao.RESTAURACAO).exists()
        )

    def test_restaurar_arquivo_inexistente_levanta_erro(self):
        registro = RegistroBackup.objects.create(nome_arquivo='nao_existe.sql', tamanho_bytes=10)
        with self.assertRaises(services.ErroDeBackup):
            services.restaurar_backup(registro, usuario=None)


class ExcluirELimparBackupTests(TestCase):
    def test_excluir_remove_arquivo_e_registro(self):
        registro = services.gerar_backup(usuario=None)
        caminho = registro.caminho_arquivo()
        self.assertTrue(caminho.is_file())
        services.excluir_backup(registro)
        self.assertFalse(caminho.is_file())
        self.assertFalse(RegistroBackup.objects.filter(pk=registro.pk).exists())

    def test_limpar_backups_antigos_remove_so_os_vencidos(self):
        recente = services.gerar_backup(usuario=None)
        antigo = services.gerar_backup(usuario=None)
        RegistroBackup.objects.filter(pk=antigo.pk).update(
            criado_em=timezone.now() - timedelta(days=40)
        )

        quantidade = services.limpar_backups_antigos(dias=30)

        self.assertEqual(quantidade, 1)
        self.assertTrue(RegistroBackup.objects.filter(pk=recente.pk).exists())
        self.assertFalse(RegistroBackup.objects.filter(pk=antigo.pk).exists())


class BackupViewsTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin17b', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin17b', password=self.senha)

    def test_gerar_via_post_cria_backup_e_redireciona(self):
        contagem_antes = RegistroBackup.objects.count()
        resposta = self.client.post(reverse('backup:gerar'))
        self.assertRedirects(resposta, reverse('backup:lista'))
        self.assertEqual(RegistroBackup.objects.count(), contagem_antes + 1)

    def test_baixar_retorna_arquivo(self):
        registro = services.gerar_backup(usuario=self.admin)
        resposta = self.client.get(reverse('backup:baixar', args=[registro.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(registro.nome_arquivo, resposta['Content-Disposition'])

    def test_baixar_arquivo_ausente_retorna_404(self):
        registro = RegistroBackup.objects.create(nome_arquivo='fantasma.sql', tamanho_bytes=1)
        resposta = self.client.get(reverse('backup:baixar', args=[registro.pk]))
        self.assertEqual(resposta.status_code, 404)

    def test_restaurar_com_confirmacao_errada_nao_restaura(self):
        Professor.objects.create(nome='Gustavo Backup', matricula='BKP002', carga_horaria=10)
        registro = services.gerar_backup(usuario=self.admin)
        Professor.objects.filter(matricula='BKP002').delete()

        resposta = self.client.post(
            reverse('backup:restaurar', args=[registro.pk]), {'confirmacao': 'nome-errado.sql'}
        )
        self.assertRedirects(resposta, reverse('backup:lista'))
        self.assertFalse(Professor.objects.filter(matricula='BKP002').exists())

    def test_excluir_via_post_remove_backup(self):
        registro = services.gerar_backup(usuario=self.admin)
        resposta = self.client.post(reverse('backup:excluir', args=[registro.pk]))
        self.assertRedirects(resposta, reverse('backup:lista'))
        self.assertFalse(RegistroBackup.objects.filter(pk=registro.pk).exists())


class BackupViewRestaurarTests(TransactionTestCase):
    """
    Em classe separada (TransactionTestCase) pelo mesmo motivo de
    `RestaurarBackupServiceTests`: essa view chama `psql` de verdade.
    """
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin17c', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin17c', password=self.senha)

    def test_restaurar_com_confirmacao_certa_restaura(self):
        Professor.objects.create(nome='Helena Backup', matricula='BKP003', carga_horaria=10)
        registro = services.gerar_backup(usuario=self.admin)
        Professor.objects.filter(matricula='BKP003').delete()

        resposta = self.client.post(
            reverse('backup:restaurar', args=[registro.pk]), {'confirmacao': registro.nome_arquivo}
        )
        self.assertRedirects(resposta, reverse('backup:lista'))
        self.assertTrue(Professor.objects.filter(matricula='BKP003').exists())
