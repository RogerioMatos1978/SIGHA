"""
Comando de gerenciamento: carrega uma grade de aulas de exemplo no
sistema, para testar o SIGHA com dados realistas em vez de cadastrar
tudo manualmente.

Cobre as três etapas da Educação Básica, na divisão oficial do MEC/LDB
(pesquisada em sabertecnologias.com.br/conteudo/quais-sao-as-series-do-
ensino-fundamental-guia-completo e fontes do MEC): Ensino Fundamental I
— Anos Iniciais, 1º ao 5º ano —, Ensino Fundamental II — Anos Finais, 6º
ao 9º ano —, e Ensino Médio — 1º ao 3º ano.

Também inclui uma turma de Curso Técnico (Módulo 20), parceria com o
SENAI: o catálogo de cursos (`CursoTecnico`) e a carga horária de 1.200h
vêm do site do SENAI Goiás (conteudo.senaigoias.com.br/cursos-tecnicos)
e da lista da SEDUC-GO (goias.gov.br/educacao/lista-de-cursos-etp-com-o-
senai) — a turma de exemplo é de Técnico em Eletrotécnica, com
`codigo_evento` de exemplo (o código real é atribuído pelo sistema do
SENAI, não por este comando).

O currículo de cada turma (quais disciplinas, quantas aulas semanais de
cada uma) não foi inventado:

- Fundamental I e II: "Grade Curricular - Ensino Fundamental" do
  Colégio Fito (fito.edu.br/arquivos/Ensino-Fundamental.pdf).
- Ensino Médio: "Estrutura Curricular para o Ensino Médio" da Faculdade
  Itop (faculdadeitop.edu.br, grade_curricular_1.2.3_ano_diurno.pdf).
- Curso Técnico: disciplinas típicas de um técnico em Eletrotécnica
  (instalações, comandos e máquinas elétricas, desenho técnico,
  segurança do trabalho), com um professor especialista por disciplina —
  o mesmo modelo de staffing do Ensino Médio.

O horário das aulas (7 aulas de 50 minutos por dia, a partir das 07:00,
com intervalo depois da 3ª) segue o padrão de aula de 50 minutos adotado
em 2026 pela rede estadual de São Paulo para os anos finais do
Fundamental (Agência SP, "SP aumenta tempo de aula...") — usamos o mesmo
horário para as três etapas, por simplicidade.

No Fundamental I, uma única "professora regente" dá a maior parte das
aulas (Português, Matemática, Ciências, Geografia, História) — o modelo
real do primeiro ciclo, em que "o trabalho é desenvolvido, usualmente,
em classes com um único professor regente" (pesquisado no mesmo guia
acima). As demais turmas têm um professor por disciplina, sem
compartilhar professor entre turmas — exceto o Fundamental II (6º e 9º
Ano), que propositalmente compartilha os mesmos professores entre as
duas turmas, para também servir de exemplo de professor dando aula em
mais de uma turma.

Uso:
    python manage.py carregar_dados_exemplo            # carrega os dados
    python manage.py carregar_dados_exemplo --limpar   # remove os dados de exemplo

Idempotente: rodar de novo sem --limpar não duplica nada — se a turma
"[Exemplo] 3º Ano A" já existir, o comando avisa e não faz nada.

Por que existem duas linhas de "Língua Portuguesa" no Fundamental II (e
de "Arte")? O campo `quantidade_aulas_semana` mora em Disciplina, não em
Turma — ou seja, é um valor só, compartilhado por todas as turmas que
usam aquela disciplina. Como o 6º Ano tem 6 aulas semanais de Português
e o 9º Ano tem 5 (números reais da grade curricular usada como
referência), a única forma de representar isso corretamente no modelo
atual é ter duas disciplinas — uma para cada quantidade. Isso não é um
artifício deste comando: é o mesmo cadastro que um coordenador
precisaria fazer na tela de Disciplinas (Módulo 5) se quisesse
representar o mesmo cenário.
"""
from datetime import date, time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.algoritmo.solver import gerar_propostas_para_turma
from apps.ambientes.models import Ambiente, TipoAmbiente
from apps.calendario.models import Evento, TipoEvento
from apps.disciplinas.models import Disciplina
from apps.disponibilidade.models import DiaSemana, DisponibilidadeProfessor
from apps.grade.models import Atribuicao, GradeAula, Semestre
from apps.horarios.models import Horario
from apps.professores.models import Professor
from apps.turmas.models import CursoTecnico, EtapaEnsino, Turma, Turno

PREFIXO_TURMA = '[Exemplo] '
PREFIXO_AMBIENTE = '[Exemplo] '
PREFIXO_EVENTO = '[Exemplo] '
PREFIXO_MATRICULA = 'EX'

# Folga de carga horária sobre o mínimo necessário de cada professor —
# nenhum contrato real fica cravado exatamente no mínimo, e a folga
# também dá espaço para o algoritmo automático (Módulo 11) encontrar um
# encaixe sem precisar resolver um "quebra-cabeça perfeito" sem sobra.
FOLGA_CARGA_HORARIA = 5

# Cada item: (nome, sigla, quantidade_aulas_semana, tipo_ambiente, chave_do_professor).
# `chave_do_professor` é só uma string de agrupamento: disciplinas com a
# MESMA chave (mesmo entre turmas diferentes) são dadas pelo MESMO
# professor — é assim que o 6º e o 9º Ano acabam compartilhando
# professor de Matemática, por exemplo.
TURMAS_EXEMPLO = [
    {
        'nome': '3º Ano A', 'serie': '3º Ano', 'turno': Turno.MATUTINO,
        'etapa_ensino': EtapaEnsino.FUNDAMENTAL_1,
        'disciplinas': [
            ('Língua Portuguesa', 'EXPORT3', 7, None, 'Regente do 3º Ano A'),
            ('Matemática', 'EXMAT3', 7, None, 'Regente do 3º Ano A'),
            ('Ciências', 'EXCIE3', 3, None, 'Regente do 3º Ano A'),
            ('Geografia', 'EXGEO3', 2, None, 'Regente do 3º Ano A'),
            ('História', 'EXHIST3', 2, None, 'Regente do 3º Ano A'),
            ('Educação Física', 'EXEDF3', 2, TipoAmbiente.QUADRA, 'Ed. Física do 3º Ano A'),
            ('Inglês', 'EXING3', 2, None, 'Inglês do 3º Ano A'),
            ('Informática', 'EXINFO3', 1, TipoAmbiente.LABORATORIO, 'Informática do 3º Ano A'),
            ('Arte', 'EXART3', 2, None, 'Arte do 3º Ano A'),
            ('Música', 'EXMUS3', 2, None, 'Música do 3º Ano A'),
        ],
    },
    {
        'nome': '6º Ano A', 'serie': '6º Ano', 'turno': Turno.MATUTINO,
        'etapa_ensino': EtapaEnsino.FUNDAMENTAL_2,
        'disciplinas': [
            ('Língua Portuguesa', 'EXPORT6', 6, None, 'Português (Fund. II)'),
            ('Matemática', 'EXMAT69', 5, None, 'Matemática (Fund. II)'),
            ('Ciências', 'EXCIE69', 4, None, 'Ciências (Fund. II)'),
            ('Geografia', 'EXGEO69', 3, None, 'Geografia (Fund. II)'),
            ('História', 'EXHIST69', 3, None, 'História (Fund. II)'),
            ('Educação Física', 'EXEDF69', 2, TipoAmbiente.QUADRA, 'Ed. Física (Fund. II)'),
            ('Inglês', 'EXING69', 2, None, 'Inglês (Fund. II)'),
            ('Informática', 'EXINFO69', 1, TipoAmbiente.LABORATORIO, 'Informática (Fund. II)'),
            ('Desenho Geométrico', 'EXDESGEO', 2, None, 'Desenho Geométrico (Fund. II)'),
            ('Arte', 'EXART6', 2, None, 'Arte (Fund. II)'),
        ],
    },
    {
        'nome': '9º Ano B', 'serie': '9º Ano', 'turno': Turno.MATUTINO,
        'etapa_ensino': EtapaEnsino.FUNDAMENTAL_2,
        'disciplinas': [
            ('Língua Portuguesa', 'EXPORT9', 5, None, 'Português (Fund. II)'),
            ('Matemática', 'EXMAT69', 5, None, 'Matemática (Fund. II)'),
            ('Ciências', 'EXCIE69', 4, None, 'Ciências (Fund. II)'),
            ('Geografia', 'EXGEO69', 3, None, 'Geografia (Fund. II)'),
            ('História', 'EXHIST69', 3, None, 'História (Fund. II)'),
            ('Educação Física', 'EXEDF69', 2, TipoAmbiente.QUADRA, 'Ed. Física (Fund. II)'),
            ('Inglês', 'EXING69', 2, None, 'Inglês (Fund. II)'),
            ('Informática', 'EXINFO69', 1, TipoAmbiente.LABORATORIO, 'Informática (Fund. II)'),
            ('Desenho Geométrico', 'EXDESGEO', 2, None, 'Desenho Geométrico (Fund. II)'),
            ('Arte', 'EXART9', 1, None, 'Arte (Fund. II)'),
            ('Geometria', 'EXGEOM', 2, None, 'Geometria (Fund. II)'),
        ],
    },
    {
        'nome': '1º Ano A', 'serie': '1º Ano', 'turno': Turno.MATUTINO,
        'etapa_ensino': EtapaEnsino.MEDIO,
        'disciplinas': [
            ('Língua Portuguesa', 'EXPORTM1', 4, None, 'Português (Médio 1º Ano A)'),
            ('Arte', 'EXARTM1', 1, None, 'Arte (Médio 1º Ano A)'),
            ('Educação Física', 'EXEDFM1', 1, TipoAmbiente.QUADRA, 'Ed. Física (Médio 1º Ano A)'),
            ('Língua Inglesa', 'EXINGM1', 1, None, 'Inglês (Médio 1º Ano A)'),
            ('Matemática', 'EXMATM1', 4, None, 'Matemática (Médio 1º Ano A)'),
            ('História', 'EXHISTM1', 2, None, 'História (Médio 1º Ano A)'),
            ('Geografia', 'EXGEOM1', 2, None, 'Geografia (Médio 1º Ano A)'),
            ('Filosofia', 'EXFILM1', 1, None, 'Filosofia (Médio 1º Ano A)'),
            ('Sociologia', 'EXSOCM1', 1, None, 'Sociologia (Médio 1º Ano A)'),
            ('Biologia', 'EXBIOM1', 2, None, 'Biologia (Médio 1º Ano A)'),
            ('Química', 'EXQUIM1', 2, None, 'Química (Médio 1º Ano A)'),
            ('Física', 'EXFISM1', 2, None, 'Física (Médio 1º Ano A)'),
            ('Espanhol', 'EXESPM1', 1, None, 'Espanhol (Médio 1º Ano A)'),
            ('Redação', 'EXREDM1', 1, None, 'Redação (Médio 1º Ano A)'),
        ],
    },
    {
        'nome': 'Eletrotécnica A', 'serie': '1º Módulo', 'turno': Turno.NOTURNO,
        'etapa_ensino': EtapaEnsino.TECNICO, 'curso_tecnico': CursoTecnico.ELETROTECNICA,
        'codigo_evento': '5567-2026',
        'disciplinas': [
            ('Instalações Elétricas Prediais', 'EXIEP', 6, TipoAmbiente.LABORATORIO, 'Instalações Elétricas (Técnico Eletrotécnica A)'),
            ('Comandos Elétricos', 'EXCOMEL', 5, TipoAmbiente.LABORATORIO, 'Comandos Elétricos (Técnico Eletrotécnica A)'),
            ('Máquinas Elétricas', 'EXMAQEL', 4, TipoAmbiente.LABORATORIO, 'Máquinas Elétricas (Técnico Eletrotécnica A)'),
            ('Desenho Técnico', 'EXDESTEC', 3, None, 'Desenho Técnico (Técnico Eletrotécnica A)'),
            ('Segurança do Trabalho', 'EXSEGTRA', 2, None, 'Segurança do Trabalho (Técnico Eletrotécnica A)'),
            ('Matemática Aplicada', 'EXMATAPL', 4, None, 'Matemática Aplicada (Técnico Eletrotécnica A)'),
            ('Inglês Técnico', 'EXINGTEC', 2, None, 'Inglês Técnico (Técnico Eletrotécnica A)'),
        ],
    },
]

AMBIENTES = [
    # Capacidade 5: com 5 turmas no exemplo (uma de cada etapa do Fund./
    # Médio, mais uma extra no Fundamental II, mais a turma de Curso
    # Técnico), isso garante que o algoritmo automático (Módulo 11)
    # sempre encontra ambiente livre, mesmo se várias turmas caírem no
    # mesmo horário para o mesmo tipo de aula — a escolha de horário e a
    # escolha de ambiente são duas etapas separadas do solver (ele não
    # tenta "casar" as duas de propósito). O Curso Técnico reaproveita o
    # mesmo "Laboratório" genérico (Módulo 7 só tem um tipo LABORATORIO,
    # sem distinguir informática de elétrica).
    ('Salas de Aula', TipoAmbiente.SALA, 5),
    ('Laboratório de Informática', TipoAmbiente.LABORATORIO, 5),
    ('Quadra Poliesportiva', TipoAmbiente.QUADRA, 5),
]

# (chave_do_professor, dia_semana, posição do horário de aula que fica
# indisponível — 0 é a 1ª aula do dia, -1 é a última) — uns poucos
# exemplos de restrição real (chega mais tarde, sai mais cedo), só para
# a tela de Disponibilidade (Módulo 9) não ficar "tudo disponível o
# tempo todo", que é raro na vida real.
INDISPONIBILIDADES = [
    ('Ed. Física (Fund. II)', DiaSemana.SEGUNDA, 0),
    ('Informática (Fund. II)', DiaSemana.SEXTA, -1),
    ('Arte (Fund. II)', DiaSemana.QUARTA, 0),
    ('Física (Médio 1º Ano A)', DiaSemana.SEXTA, -1),
]


class Command(BaseCommand):
    help = (
        'Carrega uma grade de aulas de exemplo (turmas de Fundamental I, Fundamental II '
        'e Médio, currículo e horário baseados em fontes reais) para testar o sistema. '
        'Use --limpar para remover.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpar', action='store_true',
            help='Remove os dados de exemplo carregados anteriormente (não mexe nos Horários).',
        )

    def handle(self, *args, **options):
        if options['limpar']:
            self._limpar()
            return

        turma_marcadora = Turma.objects.filter(nome=f'{PREFIXO_TURMA}3º Ano A').first()
        if turma_marcadora:
            self.stdout.write(self.style.WARNING(
                'Os dados de exemplo já estão carregados (turma '
                f'"{turma_marcadora.nome}" já existe). Use --limpar antes de '
                'carregar de novo, se quiser recriá-los.'
            ))
            return

        with transaction.atomic():
            horarios = self._criar_horarios()
            ambientes = self._criar_ambientes()
            disciplinas = self._criar_disciplinas()
            professores = self._criar_professores()
            turmas = self._criar_turmas()
            self._criar_atribuicoes(turmas, disciplinas, professores)
            self._criar_disponibilidades(professores, horarios)
            self._criar_eventos()

        self.stdout.write(self.style.SUCCESS(
            f'Cadastros criados: {len(professores)} professores, {len(disciplinas)} '
            f'disciplinas, {len(turmas)} turmas, {len(ambientes)} ambientes, '
            f'{len(horarios)} horários.'
        ))

        # Geração automática (Módulo 11): mesma função que a tela usa, e o
        # resultado é salvo do mesmo jeito (GradeAula.full_clean() + save()),
        # então a grade de exemplo nasce já validada pelas mesmas regras de
        # conflito de qualquer outra aula do sistema.
        ano_letivo = timezone.now().year
        for turma in turmas.values():
            self._gerar_grade_da_turma(turma, ano_letivo)

    # -- cadastros básicos ---------------------------------------------

    def _criar_horarios(self):
        # 7 aulas de 50 min: com turmas de currículo cheio (até 30 aulas
        # semanais), usar só 6 aulas/dia (30 horários) deixaria a semana
        # sem nenhuma folga — o que torna o encaixe automático muito mais
        # difícil (às vezes impossível) quando turmas dividem professores.
        maior_ordem = Horario.objects.aggregate(maximo=Max('ordem'))['maximo'] or 0
        definicoes = [
            (1, time(7, 0), time(7, 50), False),
            (2, time(7, 50), time(8, 40), False),
            (3, time(8, 40), time(9, 30), False),
            (4, time(9, 30), time(9, 50), True),  # intervalo
            (5, time(9, 50), time(10, 40), False),
            (6, time(10, 40), time(11, 30), False),
            (7, time(11, 30), time(12, 20), False),
            (8, time(12, 20), time(13, 10), False),
        ]
        horarios = []
        for deslocamento, inicio, fim, intervalo in definicoes:
            horario = Horario.objects.create(
                ordem=maior_ordem + deslocamento, inicio=inicio, fim=fim, intervalo=intervalo,
            )
            horarios.append(horario)
        return horarios

    def _criar_ambientes(self):
        ambientes = {}
        for nome, tipo, capacidade in AMBIENTES:
            ambiente, _ = Ambiente.objects.get_or_create(
                nome=f'{PREFIXO_AMBIENTE}{nome}', defaults={'tipo': tipo, 'capacidade': capacidade},
            )
            ambientes[nome] = ambiente
        return ambientes

    def _todas_disciplinas(self):
        """Achata TURMAS_EXEMPLO numa lista única de tuplas de disciplina."""
        for turma_spec in TURMAS_EXEMPLO:
            for item in turma_spec['disciplinas']:
                yield item

    def _criar_disciplinas(self):
        disciplinas = {}
        for nome, sigla, quantidade, tipo_ambiente, _chave in self._todas_disciplinas():
            if sigla in disciplinas:
                continue
            disciplina, _ = Disciplina.objects.get_or_create(
                sigla=sigla,
                defaults={
                    'nome': nome, 'quantidade_aulas_semana': quantidade, 'tipo_ambiente': tipo_ambiente,
                },
            )
            disciplinas[sigla] = disciplina
        return disciplinas

    def _criar_professores(self):
        # Carga horária de cada professor = soma das aulas de todas as
        # disciplinas com essa mesma chave (que pode vir de uma turma só,
        # ou de várias — caso do Fundamental II), mais a folga padrão.
        carga_por_chave = {}
        for _nome, _sigla, quantidade, _tipo, chave in self._todas_disciplinas():
            carga_por_chave[chave] = carga_por_chave.get(chave, 0) + quantidade

        professores = {}
        for indice, chave in enumerate(carga_por_chave, start=1):
            matricula = f'{PREFIXO_MATRICULA}{indice:04d}'
            professor, _ = Professor.objects.get_or_create(
                matricula=matricula,
                defaults={
                    'nome': f'Prof(a). {chave} (exemplo)',
                    'carga_horaria': carga_por_chave[chave] + FOLGA_CARGA_HORARIA,
                },
            )
            professores[chave] = professor
        return professores

    def _criar_turmas(self):
        turmas = {}
        for turma_spec in TURMAS_EXEMPLO:
            turma, _ = Turma.objects.get_or_create(
                nome=f"{PREFIXO_TURMA}{turma_spec['nome']}", turno=turma_spec['turno'],
                defaults={
                    'serie': turma_spec['serie'], 'etapa_ensino': turma_spec['etapa_ensino'],
                    'curso_tecnico': turma_spec.get('curso_tecnico', ''),
                    'codigo_evento': turma_spec.get('codigo_evento', ''),
                },
            )
            turmas[turma_spec['nome']] = turma
        return turmas

    def _criar_atribuicoes(self, turmas, disciplinas, professores):
        for turma_spec in TURMAS_EXEMPLO:
            turma = turmas[turma_spec['nome']]
            for _nome, sigla, _quantidade, _tipo, chave in turma_spec['disciplinas']:
                disciplina = disciplinas[sigla]
                professor = professores[chave]
                Atribuicao.objects.get_or_create(turma=turma, disciplina=disciplina, defaults={'professor': professor})

    def _criar_disponibilidades(self, professores, horarios):
        horarios_de_aula = [h for h in horarios if not h.intervalo]
        for chave, dia_semana, posicao in INDISPONIBILIDADES:
            professor = professores.get(chave)
            if professor is None:
                continue
            horario = horarios_de_aula[posicao]
            DisponibilidadeProfessor.objects.get_or_create(
                professor=professor, dia_semana=dia_semana, horario=horario, defaults={'disponivel': False},
            )

    def _criar_eventos(self):
        ano = timezone.now().year
        eventos = [
            (f'{PREFIXO_EVENTO}Feriado — Independência do Brasil', TipoEvento.FERIADO, date(ano, 9, 7), True),
            (f'{PREFIXO_EVENTO}Feriado — Nossa Senhora Aparecida', TipoEvento.FERIADO, date(ano, 10, 12), True),
            (f'{PREFIXO_EVENTO}Reunião pedagógica — 3º bimestre', TipoEvento.REUNIAO, date(ano, 10, 15), False),
            (f'{PREFIXO_EVENTO}Prova bimestral — Matemática', TipoEvento.PROVA, date(ano, 9, 21), False),
        ]
        for titulo, tipo, data_inicio, afeta_aulas in eventos:
            Evento.objects.get_or_create(
                titulo=titulo, data_inicio=data_inicio,
                defaults={'tipo': tipo, 'afeta_aulas': afeta_aulas, 'ano_letivo': ano},
            )

    # -- geração automática ---------------------------------------------

    def _gerar_grade_da_turma(self, turma, ano_letivo):
        resultado = gerar_propostas_para_turma(turma, ano_letivo, Semestre.PRIMEIRO)
        criadas = 0
        for proposta in resultado['propostas']:
            aula = GradeAula(
                turma=proposta['turma'], disciplina=proposta['disciplina'], professor=proposta['professor'],
                ambiente=proposta['ambiente'], dia_semana=proposta['dia_semana'], horario=proposta['horario'],
                ano_letivo=ano_letivo, semestre=Semestre.PRIMEIRO,
            )
            aula.full_clean()
            aula.save()
            criadas += 1

        self.stdout.write(f'  {turma.nome}: {criadas} aula(s) geradas automaticamente.')
        if resultado['incompletas']:
            for item in resultado['incompletas']:
                self.stdout.write(self.style.WARNING(
                    f"    faltou encaixar {item['faltantes']}x {item['disciplina'].sigla} "
                    f"({item['professor'].nome})"
                ))
        if resultado['sem_ambiente']:
            for item in resultado['sem_ambiente']:
                self.stdout.write(self.style.WARNING(
                    f"    sem ambiente livre para {item['disciplina'].sigla} em "
                    f"{item['dia_semana']} ({item['horario']})"
                ))

    # -- limpeza ----------------------------------------------------------

    def _limpar(self):
        Turma.objects.filter(nome__startswith=PREFIXO_TURMA).delete()
        # Turma.delete() em cascata já apaga as Atribuicao e GradeAula
        # dessas turmas (on_delete=CASCADE), liberando os PROTECT de
        # Professor/Disciplina/Ambiente abaixo.
        Professor.objects.filter(matricula__startswith=PREFIXO_MATRICULA).delete()
        Disciplina.objects.filter(sigla__startswith='EX').delete()
        Ambiente.objects.filter(nome__startswith=PREFIXO_AMBIENTE).delete()
        Evento.objects.filter(titulo__startswith=PREFIXO_EVENTO).delete()
        self.stdout.write(self.style.SUCCESS(
            'Dados de exemplo removidos (os Horários cadastrados não foram alterados).'
        ))
