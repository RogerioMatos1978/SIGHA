"""
Testes do módulo Calendário: permissões, o serviço de montagem do mês e
de resumo do dia, e o CRUD de eventos.
"""
import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.ambientes.models import Ambiente, TipoAmbiente
from apps.disciplinas.models import Disciplina
from apps.disponibilidade.models import DiaSemana
from apps.grade.models import GradeAula, Semestre
from apps.horarios.models import Horario
from apps.professores.models import Professor
from apps.turmas.models import Turma, Turno
from apps.usuarios.models import Papel, Usuario

from . import services
from .models import Evento, TipoEvento


class CalendarioPermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.secretaria = Usuario.objects.create_user(username='sec12', password=self.senha, papel=Papel.SECRETARIA)
        self.professor_user = Usuario.objects.create_user(username='prof12', password=self.senha, papel=Papel.PROFESSOR)

    def test_secretaria_acessa_calendario(self):
        self.client.login(username='sec12', password=self.senha)
        resposta = self.client.get(reverse('calendario:mes'))
        self.assertEqual(resposta.status_code, 200)

    def test_professor_nao_acessa_calendario(self):
        self.client.login(username='prof12', password=self.senha)
        resposta = self.client.get(reverse('calendario:mes'))
        self.assertEqual(resposta.status_code, 403)

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('calendario:mes'))
        self.assertEqual(resposta.status_code, 302)


class EventoModeloTests(TestCase):
    def test_data_fim_antes_do_inicio_nao_permite(self):
        evento = Evento(
            titulo='Teste', tipo=TipoEvento.EVENTO,
            data_inicio=datetime.date(2026, 8, 10), data_fim=datetime.date(2026, 8, 5),
        )
        with self.assertRaises(ValidationError):
            evento.full_clean()

    def test_fim_efetivo_usa_data_inicio_quando_nao_tem_fim(self):
        evento = Evento.objects.create(titulo='Feriado', tipo=TipoEvento.FERIADO, data_inicio=datetime.date(2026, 9, 7))
        self.assertEqual(evento.fim_efetivo, datetime.date(2026, 9, 7))


class MontarMesTests(TestCase):
    def test_semanas_comecam_na_segunda_e_cobrem_o_mes_todo(self):
        semanas = services.montar_mes(2026, 8)  # agosto de 2026
        self.assertTrue(all(len(semana) == 7 for semana in semanas))
        primeiro_dia_mes = min(d['data'] for semana in semanas for d in semana if d['no_mes'])
        ultimo_dia_mes = max(d['data'] for semana in semanas for d in semana if d['no_mes'])
        self.assertEqual(primeiro_dia_mes, datetime.date(2026, 8, 1))
        self.assertEqual(ultimo_dia_mes, datetime.date(2026, 8, 31))

    def test_evento_aparece_no_dia_correto(self):
        Evento.objects.create(titulo='Independência', tipo=TipoEvento.FERIADO, data_inicio=datetime.date(2026, 9, 7), afeta_aulas=True)
        semanas = services.montar_mes(2026, 9)
        dia_7 = next(d for semana in semanas for d in semana if d['data'] == datetime.date(2026, 9, 7))
        self.assertEqual(len(dia_7['eventos']), 1)
        self.assertEqual(dia_7['eventos'][0].titulo, 'Independência')

    def test_evento_de_varios_dias_aparece_em_todos_eles(self):
        Evento.objects.create(
            titulo='Recesso', tipo=TipoEvento.RECESSO,
            data_inicio=datetime.date(2026, 7, 20), data_fim=datetime.date(2026, 7, 24), afeta_aulas=True,
        )
        semanas = services.montar_mes(2026, 7)
        dias_com_evento = [
            d['data'] for semana in semanas for d in semana
            if any(e.titulo == 'Recesso' for e in d['eventos'])
        ]
        self.assertEqual(len(dias_com_evento), 5)


class ResumoDoDiaTests(TestCase):
    def setUp(self):
        self.turma = Turma.objects.create(nome='1º Ano A', serie='1º Ano', turno=Turno.MATUTINO)
        self.disciplina = Disciplina.objects.create(nome='Matemática', sigla='MAT', quantidade_aulas_semana=3)
        self.professor = Professor.objects.create(nome='Ana', matricula='CAL001', carga_horaria=20)
        self.ambiente = Ambiente.objects.create(nome='Sala Cal', tipo=TipoAmbiente.SALA, capacidade=1)
        self.horario = Horario.objects.create(ordem=1, inicio=datetime.time(7, 0), fim=datetime.time(7, 50))
        # 2026-08-03 é uma segunda-feira
        self.segunda = datetime.date(2026, 8, 3)
        GradeAula.objects.create(
            turma=self.turma, disciplina=self.disciplina, professor=self.professor, ambiente=self.ambiente,
            dia_semana=DiaSemana.SEGUNDA, horario=self.horario, ano_letivo=2026, semestre=Semestre.SEGUNDO,
        )

    def test_dia_letivo_mostra_aulas_previstas(self):
        resumo = services.resumo_do_dia(self.segunda)
        self.assertTrue(resumo['dia_letivo'])
        self.assertEqual(len(resumo['aulas']), 1)
        self.assertEqual(resumo['aulas'][0].disciplina, self.disciplina)

    def test_feriado_marca_dia_como_nao_letivo_e_esconde_aulas(self):
        Evento.objects.create(titulo='Feriado local', tipo=TipoEvento.FERIADO, data_inicio=self.segunda, afeta_aulas=True)
        resumo = services.resumo_do_dia(self.segunda)
        self.assertFalse(resumo['dia_letivo'])
        self.assertEqual(resumo['aulas'], [])

    def test_evento_que_nao_afeta_aulas_nao_esconde_aulas(self):
        Evento.objects.create(titulo='Reunião', tipo=TipoEvento.REUNIAO, data_inicio=self.segunda, afeta_aulas=False)
        resumo = services.resumo_do_dia(self.segunda)
        self.assertTrue(resumo['dia_letivo'])
        self.assertEqual(len(resumo['aulas']), 1)

    def test_fim_de_semana_nao_e_dia_letivo(self):
        sabado = datetime.date(2026, 8, 8)
        resumo = services.resumo_do_dia(sabado)
        self.assertFalse(resumo['dia_letivo'])


class EventoCrudViewsTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin12', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin12', password=self.senha)

    def test_criar_evento(self):
        resposta = self.client.post(reverse('calendario:evento_criar'), {
            'titulo': 'Prova bimestral', 'tipo': TipoEvento.PROVA,
            'data_inicio': '2026-09-15', 'descricao': '', 'ano_letivo': 2026,
        })
        self.assertEqual(resposta.status_code, 302)
        evento = Evento.objects.get(titulo='Prova bimestral')
        self.assertEqual(evento.criado_por, self.admin)

    def test_data_fim_invalida_mostra_erro_sem_salvar(self):
        resposta = self.client.post(reverse('calendario:evento_criar'), {
            'titulo': 'Evento inválido', 'tipo': TipoEvento.EVENTO,
            'data_inicio': '2026-09-15', 'data_fim': '2026-09-10', 'ano_letivo': 2026,
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Evento.objects.filter(titulo='Evento inválido').exists())

    def test_editar_evento(self):
        evento = Evento.objects.create(titulo='Original', tipo=TipoEvento.EVENTO, data_inicio=datetime.date(2026, 10, 1))
        resposta = self.client.post(reverse('calendario:evento_editar', args=[evento.pk]), {
            'titulo': 'Alterado', 'tipo': TipoEvento.EVENTO,
            'data_inicio': '2026-10-01', 'ano_letivo': 2026,
        })
        self.assertEqual(resposta.status_code, 302)
        evento.refresh_from_db()
        self.assertEqual(evento.titulo, 'Alterado')

    def test_remover_evento(self):
        evento = Evento.objects.create(titulo='Para remover', tipo=TipoEvento.EVENTO, data_inicio=datetime.date(2026, 10, 1))
        resposta = self.client.post(reverse('calendario:evento_remover', args=[evento.pk]))
        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(Evento.objects.filter(pk=evento.pk).exists())

    def test_dia_detalhe_mostra_evento(self):
        Evento.objects.create(titulo='Dia especial', tipo=TipoEvento.EVENTO, data_inicio=datetime.date(2026, 10, 12))
        resposta = self.client.get(reverse('calendario:dia', args=[2026, 10, 12]))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Dia especial')

    def test_data_invalida_no_dia_detalhe_retorna_404(self):
        resposta = self.client.get(reverse('calendario:dia', args=[2026, 2, 30]))
        self.assertEqual(resposta.status_code, 404)
