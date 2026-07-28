"""
Testes do módulo Algoritmo automático: permissões, o solver (OR-Tools) em
si — respeita disponibilidade, carga horária, conflitos com outras
turmas e capacidade de ambiente — e a view completa de geração.
"""
import datetime

from django.test import TestCase
from django.urls import reverse

from apps.ambientes.models import Ambiente, TipoAmbiente
from apps.disciplinas.models import Disciplina
from apps.disponibilidade.models import DiaSemana, DisponibilidadeProfessor
from apps.grade.models import Atribuicao, GradeAula, Semestre
from apps.horarios.models import Horario
from apps.professores.models import Professor
from apps.turmas.models import Turma, Turno
from apps.usuarios.models import Papel, Usuario

from . import solver


class AlgoritmoPermissoesTests(TestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.secretaria = Usuario.objects.create_user(username='sec11', password=self.senha, papel=Papel.SECRETARIA)
        self.professor_user = Usuario.objects.create_user(username='prof11', password=self.senha, papel=Papel.PROFESSOR)

    def test_secretaria_acessa_lista(self):
        self.client.login(username='sec11', password=self.senha)
        resposta = self.client.get(reverse('algoritmo:lista'))
        self.assertEqual(resposta.status_code, 200)

    def test_professor_nao_acessa_lista(self):
        self.client.login(username='prof11', password=self.senha)
        resposta = self.client.get(reverse('algoritmo:lista'))
        self.assertEqual(resposta.status_code, 403)

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('algoritmo:lista'))
        self.assertEqual(resposta.status_code, 302)


class SolverBaseTestCase(TestCase):
    def setUp(self):
        self.turma = Turma.objects.create(nome='1º Ano A', serie='1º Ano', turno=Turno.MATUTINO)
        self.disciplina = Disciplina.objects.create(nome='Matemática', sigla='MAT', quantidade_aulas_semana=3)
        self.professor = Professor.objects.create(nome='Ana Souza', matricula='ALG001', carga_horaria=20)
        self.ambiente = Ambiente.objects.create(nome='Sala 1', tipo=TipoAmbiente.SALA, capacidade=1)
        self.horarios = [
            Horario.objects.create(ordem=i, inicio=datetime.time(7 + i, 0), fim=datetime.time(7 + i, 50))
            for i in range(1, 4)
        ]
        self.atribuicao = Atribuicao.objects.create(
            turma=self.turma, disciplina=self.disciplina, professor=self.professor,
        )


class SolverTests(SolverBaseTestCase):
    def test_gera_todas_as_aulas_quando_ha_espaco_suficiente(self):
        resultado = solver.gerar_propostas_para_turma(self.turma, 2026, Semestre.PRIMEIRO)
        self.assertEqual(len(resultado['propostas']), 3)
        self.assertEqual(resultado['incompletas'], [])
        self.assertEqual(resultado['sem_ambiente'], [])
        # nenhum horario repetido para a mesma turma
        slots = {(p['dia_semana'], p['horario'].id) for p in resultado['propostas']}
        self.assertEqual(len(slots), 3)

    def test_respeita_indisponibilidade_do_professor(self):
        # bloqueia o professor em todos os horarios de segunda-feira
        for horario in self.horarios:
            DisponibilidadeProfessor.objects.create(
                professor=self.professor, dia_semana=DiaSemana.SEGUNDA, horario=horario, disponivel=False,
            )
        resultado = solver.gerar_propostas_para_turma(self.turma, 2026, Semestre.PRIMEIRO)
        dias_usados = {p['dia_semana'] for p in resultado['propostas']}
        self.assertNotIn(DiaSemana.SEGUNDA, dias_usados)

    def test_respeita_carga_horaria_do_professor(self):
        self.professor.carga_horaria = 1
        self.professor.save()
        resultado = solver.gerar_propostas_para_turma(self.turma, 2026, Semestre.PRIMEIRO)
        self.assertEqual(len(resultado['propostas']), 1)
        self.assertEqual(resultado['incompletas'][0]['faltantes'], 2)

    def test_nao_conflita_com_aula_ja_existente_do_professor_em_outra_turma(self):
        outra_turma = Turma.objects.create(nome='1º Ano B', serie='1º Ano', turno=Turno.MATUTINO)
        outra_disciplina = Disciplina.objects.create(nome='Português', sigla='POR', quantidade_aulas_semana=1)
        GradeAula.objects.create(
            turma=outra_turma, disciplina=outra_disciplina, professor=self.professor, ambiente=self.ambiente,
            dia_semana=DiaSemana.SEGUNDA, horario=self.horarios[0], ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        resultado = solver.gerar_propostas_para_turma(self.turma, 2026, Semestre.PRIMEIRO)
        slots_usados = {(p['dia_semana'], p['horario'].id) for p in resultado['propostas']}
        self.assertNotIn((DiaSemana.SEGUNDA, self.horarios[0].id), slots_usados)

    def test_nao_agenda_mais_do_que_ja_falta(self):
        GradeAula.objects.create(
            turma=self.turma, disciplina=self.disciplina, professor=self.professor, ambiente=self.ambiente,
            dia_semana=DiaSemana.SEGUNDA, horario=self.horarios[0], ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        resultado = solver.gerar_propostas_para_turma(self.turma, 2026, Semestre.PRIMEIRO)
        # só faltam 2 (3 necessarias - 1 ja lancada)
        self.assertEqual(len(resultado['propostas']), 2)

    def test_sem_ambiente_disponivel_e_reportado(self):
        # ocupa a unica sala disponivel em todos os horarios/dias possiveis
        outro_professor = Professor.objects.create(nome='Outro', matricula='ALG002', carga_horaria=40)
        contador = 0
        for dia, _rotulo in DiaSemana.choices:
            for horario in self.horarios:
                contador += 1
                GradeAula.objects.create(
                    turma=Turma.objects.create(nome=f'Ocupa {contador}', serie='X', turno=Turno.VESPERTINO),
                    disciplina=Disciplina.objects.create(nome=f'Disc {contador}', sigla=f'D{contador}', quantidade_aulas_semana=1),
                    professor=outro_professor, ambiente=self.ambiente,
                    dia_semana=dia, horario=horario, ano_letivo=2026, semestre=Semestre.PRIMEIRO,
                )
        resultado = solver.gerar_propostas_para_turma(self.turma, 2026, Semestre.PRIMEIRO)
        self.assertEqual(resultado['propostas'], [])
        self.assertTrue(len(resultado['sem_ambiente']) > 0)

    def test_resumo_atribuicoes_mostra_faltantes(self):
        resumo = solver.resumo_atribuicoes(self.turma, 2026, Semestre.PRIMEIRO)
        self.assertEqual(len(resumo), 1)
        self.assertEqual(resumo[0]['necessarias'], 3)
        self.assertEqual(resumo[0]['alocadas'], 0)
        self.assertEqual(resumo[0]['faltantes'], 3)


class GerarGradeViewTests(SolverBaseTestCase):
    def setUp(self):
        super().setUp()
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(username='admin11', password=self.senha, papel=Papel.ADMINISTRADOR)
        self.client.login(username='admin11', password=self.senha)

    def test_get_mostra_resumo(self):
        resposta = self.client.get(reverse('algoritmo:gerar', args=[self.turma.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Matemática')

    def test_post_gera_e_salva_aulas(self):
        resposta = self.client.post(reverse('algoritmo:gerar', args=[self.turma.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(GradeAula.objects.filter(turma=self.turma).count(), 3)

    def test_post_com_limpar_existentes_apaga_antes_de_gerar(self):
        GradeAula.objects.create(
            turma=self.turma, disciplina=self.disciplina, professor=self.professor, ambiente=self.ambiente,
            dia_semana=DiaSemana.SEXTA, horario=self.horarios[2], ano_letivo=2026, semestre=Semestre.PRIMEIRO,
        )
        self.client.post(reverse('algoritmo:gerar', args=[self.turma.pk]), {'limpar_existentes': 'on'})
        # apagou a aula antiga de sexta e recriou 3 do zero
        aulas = GradeAula.objects.filter(turma=self.turma)
        self.assertEqual(aulas.count(), 3)
