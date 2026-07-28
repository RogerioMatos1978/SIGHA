"""
Módulo 18 (Testes) — teste de integração de ponta a ponta.

Cada um dos 17 módulos anteriores já tem sua própria suíte, testando
sua fatia isoladamente (ex.: "o modelo Professor valida X",
"a view de Turmas bloqueia quem não pode gerenciar académico"). O que
falta — e é o que este arquivo cobre — é provar que as peças realmente
se encaixam quando usadas juntas, na ordem em que uma escola de verdade
usaria o sistema:

    cadastros básicos (4–9) → atribuições (10) → geração automática (11)
    → grade visual (10) → relatórios (13) → exportação (14) → API (15)
    → auditoria (16) → backup/restauração (17)

Não substitui as suítes de cada módulo — é a prova de que a integração
entre eles não quebrou.

TransactionTestCase (não TestCase): a etapa de backup roda `psql` num
processo externo, que precisa de lock exclusivo nas tabelas — dentro de
um TestCase comum (que embrulha o teste inteiro numa transação aberta) o
psql ficaria esperando esse lock para sempre. Mesmo motivo documentado em
`apps/backup/tests.py`.
"""
from datetime import time

from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from apps.ambientes.models import Ambiente, TipoAmbiente
from apps.auditoria.models import Acao, RegistroAuditoria
from apps.backup import services as backup_services
from apps.disciplinas.models import Disciplina
from apps.grade.models import Atribuicao, GradeAula, Semestre
from apps.horarios.models import Horario
from apps.professores.models import Professor
from apps.turmas.models import Turma, Turno
from apps.usuarios.models import Papel, Usuario


class FluxoCompletoTests(TransactionTestCase):
    def setUp(self):
        self.senha = 'SenhaForte123'
        self.admin = Usuario.objects.create_user(
            username='e2e_admin', password=self.senha, papel=Papel.ADMINISTRADOR,
        )
        self.client.login(username='e2e_admin', password=self.senha)
        self.ano_letivo = timezone.now().year
        self.semestre = Semestre.PRIMEIRO

    def test_fluxo_completo_de_cadastro_a_backup(self):
        # 1) Cadastros básicos (Módulos 4 a 8) — a base de tudo o que vem depois.
        professor = Professor.objects.create(
            nome='Fluxo Completo', matricula='E2E001', carga_horaria=4,
        )
        disciplina = Disciplina.objects.create(
            nome='Matemática E2E', sigla='MATE2E', quantidade_aulas_semana=2,
        )
        turma = Turma.objects.create(nome='E2E Ano A', serie='E2E', turno=Turno.MATUTINO)
        ambiente = Ambiente.objects.create(
            nome='Sala E2E', tipo=TipoAmbiente.SALA, capacidade=1,
        )
        horarios = [
            Horario.objects.create(ordem=100 + i, inicio=time(7 + i, 0), fim=time(7 + i, 50))
            for i in range(3)
        ]
        self.assertEqual(Horario.objects.filter(pk__in=[h.pk for h in horarios]).count(), 3)

        # Disponibilidade (Módulo 9): nenhuma restrição cadastrada = professor
        # disponível em tudo (regra padrão validada em apps/disponibilidade).

        # 2) Atribuição (Módulo 10): quem dá o quê para qual turma.
        Atribuicao.objects.create(turma=turma, disciplina=disciplina, professor=professor)

        # 3) Algoritmo automático (Módulo 11) — via view real (POST), não
        # chamando o solver direto, para provar a integração view+solver
        # +GradeAula.full_clean() como um usuário de verdade dispararia.
        resposta = self.client.post(reverse('algoritmo:gerar', args=[turma.pk]))
        self.assertEqual(resposta.status_code, 200)

        aulas_geradas = GradeAula.objects.filter(
            turma=turma, ano_letivo=self.ano_letivo, semestre=self.semestre,
        )
        self.assertEqual(
            aulas_geradas.count(), disciplina.quantidade_aulas_semana,
            'O solver deveria ter encaixado as 2 aulas semanais da disciplina '
            '(professor livre, ambiente livre, 15 horários possíveis).',
        )
        for aula in aulas_geradas:
            self.assertEqual(aula.professor_id, professor.pk)
            self.assertEqual(aula.ambiente_id, ambiente.pk)

        # 4) Grade visual (Módulo 10): o grid reflete exatamente o que foi gerado.
        from apps.grade.services import montar_grade_turma
        grade = montar_grade_turma(turma, self.ano_letivo, self.semestre)
        celulas_preenchidas = [
            aula for linha in grade.values() for aula in linha.values() if aula is not None
        ]
        self.assertEqual(len(celulas_preenchidas), disciplina.quantidade_aulas_semana)

        # 5) Relatório de pendências (Módulo 13): a turma não deve ter mais
        # faltantes, já que o algoritmo encaixou tudo que era necessário.
        from apps.relatorios.services import relatorio_pendencias_por_turma
        pendencias = relatorio_pendencias_por_turma(self.ano_letivo, self.semestre)
        linha_turma = next(item for item in pendencias if item['turma'].pk == turma.pk)
        self.assertEqual(linha_turma['faltantes'], 0)
        self.assertTrue(linha_turma['completa'])

        # 6) Exportação (Módulo 14): a grade dessa turma sai em Excel de verdade.
        resposta_excel = self.client.get(
            reverse('exportacoes:grade_turma', args=[turma.pk, 'excel'])
        )
        self.assertEqual(resposta_excel.status_code, 200)
        self.assertEqual(
            resposta_excel['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        # 7) API (Módulo 15): as mesmas aulas aparecem por /api/v1/grade/.
        resposta_api = self.client.get('/api/v1/grade/', {'turma': turma.pk})
        self.assertEqual(resposta_api.status_code, 200)
        dados_api = resposta_api.json()
        # A API não pagina por padrão (REST_FRAMEWORK sem DEFAULT_PAGINATION_CLASS),
        # então a resposta é uma lista simples — só trata o formato paginado
        # como bônus, caso isso mude no futuro.
        resultados = dados_api.get('results', []) if isinstance(dados_api, dict) else dados_api
        self.assertEqual(len(resultados), disciplina.quantidade_aulas_semana)

        # 8) Auditoria (Módulo 16): cadastro e geração automática, tudo logado
        # sem que nenhuma view precisasse saber que a Auditoria existe.
        self.assertTrue(
            RegistroAuditoria.objects.filter(modelo='Professor', acao=Acao.CRIACAO, objeto_id=str(professor.pk)).exists()
        )
        self.assertEqual(
            RegistroAuditoria.objects.filter(modelo='GradeAula', acao=Acao.CRIACAO).count(),
            disciplina.quantidade_aulas_semana,
        )

        # 9) Backup e restauração (Módulo 17): o momento da verdade — gera um
        # backup do estado atual, apaga o professor (o que barraria a grade
        # inteira, já que GradeAula.professor é PROTECT), restaura, e tudo
        # volta a existir exatamente como estava.
        backup = backup_services.gerar_backup(usuario=self.admin)
        self.assertTrue(backup.existe_no_disco())

        professor_id = professor.pk
        aulas_ids = list(aulas_geradas.values_list('pk', flat=True))
        with self.assertRaises(Exception):
            # PROTECT: não deveria nem deixar apagar com aulas dependentes —
            # confirma que a integridade referencial entre módulos está de pé.
            professor.delete()

        # Restauração de verdade: apaga a aula (agora sim é possível apagar o
        # professor) e comprova que o backup traz a aula de volta também.
        GradeAula.objects.filter(pk__in=aulas_ids).delete()
        Professor.objects.filter(pk=professor_id).delete()
        self.assertFalse(Professor.objects.filter(pk=professor_id).exists())
        self.assertEqual(GradeAula.objects.filter(pk__in=aulas_ids).count(), 0)

        backup_services.restaurar_backup(backup, usuario=self.admin)

        self.assertTrue(Professor.objects.filter(pk=professor_id).exists())
        self.assertEqual(GradeAula.objects.filter(pk__in=aulas_ids).count(), len(aulas_ids))
        self.assertTrue(
            RegistroAuditoria.objects.filter(modelo='RegistroBackup', acao=Acao.RESTAURACAO).exists()
        )

        # 10) Dashboard (Módulo 3): a tela inicial sobe normalmente depois de
        # tudo isso, sem erro 500 — o "ainda funciona de ponta a ponta".
        resposta_dashboard = self.client.get(reverse('home'))
        self.assertEqual(resposta_dashboard.status_code, 200)
