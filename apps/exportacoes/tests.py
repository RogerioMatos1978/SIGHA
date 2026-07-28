"""
Testes do módulo Exportações: permissões, os geradores de cada formato
(bytes válidos e com a assinatura/tamanho esperado) e as views (status,
content-type e content-disposition corretos).
"""
import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.ambientes.models import Ambiente, TipoAmbiente
from apps.disciplinas.models import Disciplina
from apps.disponibilidade.models import DiaSemana
from apps.grade.models import GradeAula, Semestre
from apps.grade import services as grade_services
from apps.horarios.models import Horario
from apps.professores.models import Professor
from apps.relatorios import services as relatorios_services
from apps.turmas.models import Turma, Turno
from apps.usuarios.models import Papel, Usuario

from . import services
from .excel import gerar_excel_grade
from .imagem import gerar_imagem_grade
from .pdf import gerar_pdf_grade
from .word import gerar_docx_grade


class ExportacoesBaseTestCase(TestCase):
    def setUp(self):
        self.turma = Turma.objects.create(nome='1º Ano A', serie='1º Ano', turno=Turno.MATUTINO)
        self.disciplina = Disciplina.objects.create(nome='Matemática', sigla='MAT', quantidade_aulas_semana=1)
        self.professor = Professor.objects.create(nome='Ana Souza', matricula='EXP001', carga_horaria=10)
        self.ambiente = Ambiente.objects.create(nome='Sala Exp', tipo=TipoAmbiente.SALA, capacidade=1)
        self.horario = Horario.objects.create(ordem=1, inicio=datetime.time(7, 0), fim=datetime.time(7, 50))
        GradeAula.objects.create(
            turma=self.turma, disciplina=self.disciplina, professor=self.professor, ambiente=self.ambiente,
            dia_semana=DiaSemana.SEGUNDA, horario=self.horario, ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        self.grid_turma = grade_services.montar_grade_turma(self.turma, 2026, Semestre.PRIMEIRO)
        self.grid_professor = relatorios_services.grade_semanal_do_professor(self.professor, 2026, Semestre.PRIMEIRO)


class GeradoresTests(ExportacoesBaseTestCase):
    def test_excel_gera_arquivo_com_assinatura_valida(self):
        buffer = gerar_excel_grade('Grade teste', DiaSemana.choices, self.grid_turma, services.linhas_celula_turma)
        conteudo = buffer.getvalue()
        self.assertTrue(len(conteudo) > 0)
        self.assertEqual(conteudo[:2], b'PK')  # xlsx é um zip

    def test_pdf_gera_arquivo_com_assinatura_valida(self):
        buffer = gerar_pdf_grade('Grade teste', DiaSemana.choices, self.grid_turma, services.linhas_celula_turma)
        conteudo = buffer.getvalue()
        self.assertTrue(len(conteudo) > 0)
        self.assertTrue(conteudo.startswith(b'%PDF'))

    def test_word_gera_arquivo_com_assinatura_valida(self):
        buffer = gerar_docx_grade('Grade teste', DiaSemana.choices, self.grid_turma, services.linhas_celula_turma)
        conteudo = buffer.getvalue()
        self.assertTrue(len(conteudo) > 0)
        self.assertEqual(conteudo[:2], b'PK')  # docx também é um zip

    def test_png_gera_imagem_valida(self):
        buffer = gerar_imagem_grade('Grade teste', DiaSemana.choices, self.grid_turma, services.linhas_celula_turma, formato='PNG')
        conteudo = buffer.getvalue()
        self.assertTrue(conteudo.startswith(b'\x89PNG'))

    def test_jpeg_gera_imagem_valida(self):
        buffer = gerar_imagem_grade('Grade teste', DiaSemana.choices, self.grid_turma, services.linhas_celula_turma, formato='JPEG')
        conteudo = buffer.getvalue()
        self.assertTrue(conteudo.startswith(b'\xff\xd8'))

    def test_grade_por_professor_tambem_exporta(self):
        buffer = gerar_excel_grade('Grade professor', DiaSemana.choices, self.grid_professor, services.linhas_celula_professor)
        self.assertTrue(len(buffer.getvalue()) > 0)


class ServicoDispatchTests(ExportacoesBaseTestCase):
    def test_formato_invalido_levanta_erro(self):
        with self.assertRaises(ValidationError):
            services.gerar_arquivo('cobol', 't', DiaSemana.choices, self.grid_turma, services.linhas_celula_turma)

    def test_cada_formato_retorna_content_type_correto(self):
        esperados = {
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'pdf': 'application/pdf',
            'word': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'png': 'image/png',
            'jpeg': 'image/jpeg',
        }
        for formato, content_type_esperado in esperados.items():
            _buffer, content_type, _ext = services.gerar_arquivo(
                formato, 't', DiaSemana.choices, self.grid_turma, services.linhas_celula_turma,
            )
            self.assertEqual(content_type, content_type_esperado)


class ExportacoesPermissoesTests(ExportacoesBaseTestCase):
    def setUp(self):
        super().setUp()
        self.senha = 'SenhaForte123'
        self.secretaria = Usuario.objects.create_user(username='sec14', password=self.senha, papel=Papel.SECRETARIA)
        self.professor_user = Usuario.objects.create_user(username='prof14', password=self.senha, papel=Papel.PROFESSOR)

    def test_secretaria_exporta_grade_turma(self):
        self.client.login(username='sec14', password=self.senha)
        resposta = self.client.get(reverse('exportacoes:grade_turma', args=[self.turma.pk, 'pdf']))
        self.assertEqual(resposta.status_code, 200)

    def test_professor_nao_exporta(self):
        self.client.login(username='prof14', password=self.senha)
        resposta = self.client.get(reverse('exportacoes:grade_turma', args=[self.turma.pk, 'pdf']))
        self.assertEqual(resposta.status_code, 403)

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('exportacoes:grade_turma', args=[self.turma.pk, 'pdf']))
        self.assertEqual(resposta.status_code, 302)


class ExportacoesViewsTests(ExportacoesBaseTestCase):
    def setUp(self):
        super().setUp()
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin14', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin14', password=self.senha)

    def test_exportar_grade_turma_excel(self):
        resposta = self.client.get(
            reverse('exportacoes:grade_turma', args=[self.turma.pk, 'excel']), {'ano': 2026, 'semestre': '1'},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertIn('attachment', resposta['Content-Disposition'])
        self.assertTrue(len(resposta.content) > 0)

    def test_exportar_grade_professor_pdf(self):
        resposta = self.client.get(
            reverse('exportacoes:grade_professor', args=[self.professor.pk, 'pdf']), {'ano': 2026, 'semestre': '1'},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta['Content-Type'], 'application/pdf')

    def test_formato_invalido_retorna_400(self):
        resposta = self.client.get(reverse('exportacoes:grade_turma', args=[self.turma.pk, 'cobol']))
        self.assertEqual(resposta.status_code, 400)

    def test_turma_inexistente_retorna_404(self):
        resposta = self.client.get(reverse('exportacoes:grade_turma', args=[99999, 'pdf']))
        self.assertEqual(resposta.status_code, 404)
