# SIGHA — Sistema Inteligente de Gestão de Horários Acadêmicos

Status atual: **os 18 módulos da especificação original estão concluídos
e testados** — Usuários, Login, Dashboard, Professores, Disciplinas,
Turmas, Ambientes, Horários, Disponibilidade, Grade, Algoritmo automático
(OR-Tools), Calendário, Relatórios, Exportações, API, Auditoria, Backup e
Testes (a suíte de integração de ponta a ponta + cobertura + CI descritas
mais abaixo) — mais um **Módulo 19** de melhorias pedidas depois: etapa
de ensino em Turma, vínculo Professor↔Turma, e Substituições. O sistema
está funcional de ponta a ponta.

## O que já funciona

- Modelo de usuário próprio (`apps/usuarios`), com matrícula, telefone, papel
  (Administrador, Coordenador, Secretaria, Professor, Consulta) e status ativo/inativo.
- Login/logout com proteção contra força bruta (máx. 10 tentativas/minuto por IP),
  CSRF, cookies seguros e bloqueio de usuários inativos.
- Cadastro de usuários (listar, criar, editar, ativar/desativar) — restrito a
  Administrador e Coordenador.
- Dashboard (`apps/dashboard`) com indicadores de usuários (total, ativos,
  inativos, gráfico por papel) e cartões para os indicadores acadêmicos —
  agora que o módulo de Grade existe, todos os cartões mostram números
  reais: professores, disciplinas, turmas, ambientes, aulas já encaixadas
  na grade no ano atual, horários ainda livres e conflitos encontrados
  (sempre 0, porque o próprio sistema nunca permite salvar um conflito).
- Cadastro de professores (`apps/professores`): nome, matrícula, e-mail,
  telefone, carga horária semanal, ativo/inativo, e o **vínculo com
  turmas** (Módulo 19): em quais etapas de ensino (Fundamental I,
  Fundamental II, Médio) o professor pode lecionar, mais exceções
  pontuais por turma específica (liberar uma turma fora da etapa, ou
  bloquear uma turma dentro dela) — resolve o caso real de o professor do
  Médio não dar aula para o Fundamental, e os Fundamentais não se
  misturarem. É só um **aviso** na hora de montar a Atribuição/Grade,
  nunca um bloqueio — o coordenador sempre pode escalar alguém fora do
  vínculo num caso excepcional.
- Cadastro de disciplinas (`apps/disciplinas`): nome, sigla (normalizada
  em maiúscula automaticamente), quantidade de aulas por semana, ativo/inativo.
- Cadastro de turmas (`apps/turmas`): nome, série, etapa de ensino
  (Fundamental I, Fundamental II ou Médio — a divisão oficial do
  MEC/LDB: Fundamental I do 1º ao 5º ano, Fundamental II do 6º ao 9º,
  Médio do 1º ao 3º), turno (Matutino, Vespertino, Noturno, Integral),
  ativo/inativo — mesma turma pode existir em turnos diferentes, mas não
  duplicada no mesmo turno. A lista tem filtro por etapa de ensino.
- Cadastro de ambientes (`apps/ambientes`): nome (único), tipo (Sala,
  Biblioteca, Laboratório, Quadra, Auditório, Maker), capacidade de uso
  simultâneo, ativo/inativo — essa capacidade é o dado que o futuro módulo
  de Grade vai usar para nunca marcar duas turmas no mesmo ambiente ao
  mesmo tempo quando a capacidade for 1.
- Cadastro de horários (`apps/horarios`): ordem, início, fim, marcação de
  intervalo/recreio, ativo/inativo — os "07:00, 07:50, 08:40... Intervalo..."
  do exemplo da especificação, sempre configuráveis, nunca fixos no código.
  Valida que o fim seja depois do início e que a ordem não se repita.
- Disponibilidade de professores (`apps/disponibilidade`): para cada
  professor, uma grade com os dias da semana nas colunas e os horários de
  aula nas linhas — marque onde ele pode dar aula. Todo professor começa
  disponível em tudo; a grade é gerada automaticamente na primeira visita.
  Este é o dado que o futuro algoritmo (OR-Tools) vai usar para nunca
  escalar um professor num horário que ele marcou como indisponível.
  Todos restritos a Administrador, Coordenador e Secretaria.
- Grade (`apps/grade`): a tela principal do sistema — para cada turma, uma
  visualização estilo Excel (dias nas colunas, horários nas linhas) onde
  cada célula é uma aula (disciplina, professor, ambiente). Controlada por
  ano letivo e semestre. Nenhuma aula conflitante consegue ser salva,
  porque o próprio modelo valida antes de gravar: turma não pode ter duas
  aulas ao mesmo tempo, professor não pode estar em duas turmas ao mesmo
  tempo, o ambiente respeita sua capacidade de uso simultâneo cadastrada
  no Módulo 7, o professor respeita a própria disponibilidade cadastrada
  no Módulo 9, e o professor nunca ultrapassa a própria carga horária
  semanal cadastrada no Módulo 4. Restrito a Administrador, Coordenador e
  Secretaria. Também é onde se cadastram as **atribuições** (qual
  professor dá qual disciplina para qual turma) — a informação de entrada
  que o Módulo 11 usa para gerar a grade sozinho. Editar uma atribuição
  troca o professor **permanentemente** dali para frente (Módulo 19 —
  ex.: professor saiu de licença); se o professor escolhido estiver fora
  do vínculo etapa/turma, o sistema salva mesmo assim e só avisa.
- Substituições (`apps/substituicoes`, Módulo 19): cobre a falta pontual
  de um professor titular numa data específica, sem mexer na atribuição
  original — o mesmo fluxo usado por sistemas reais de gestão escolar
  (ex.: Sistema SIGA) para registrar quem cobriu a aula (ou que a aula
  foi cancelada, sem atendimento). Valida que a data cai no dia da semana
  certo da aula, que o substituto não é o próprio titular, e que ele não
  está em choque de horário com a grade regular ou com outra
  substituição no mesmo dia.
- Algoritmo automático (`apps/algoritmo`): botão "Gerar automaticamente"
  na tela da Grade. Usa o [OR-Tools](https://developers.google.com/optimization)
  (solver CP-SAT) para decidir o dia e o horário de cada aula das
  atribuições cadastradas, respeitando disponibilidade do professor,
  carga horária semanal e os compromissos que ele já tem em outras
  turmas; depois escolhe o ambiente de cada aula respeitando a
  capacidade cadastrada no Módulo 7. Nunca sobrescreve o que foi editado
  manualmente — só preenche o que falta — e mostra um relatório do que
  não coube (professor sem horário livre suficiente, ambiente sem vaga)
  para o coordenador decidir o que ajustar. Toda aula gerada passa pela
  mesma validação do Módulo 10, então nada conflitante é salvo.
- Calendário (`apps/calendario`): calendário mensal com feriados, recessos,
  provas, eventos e reuniões pedagógicas. Marcar um evento como "não há
  aula normal" (feriado/recesso) faz o detalhe daquele dia avisar isso e
  esconder as aulas que normalmente aconteceriam — sem precisar alterar a
  Grade recorrente por dia da semana (Módulo 10), que continua sendo o
  "modelo" semanal. Clicar num dia mostra os eventos cadastrados e, se for
  dia letivo, as aulas previstas (de todas as turmas) naquele dia da
  semana. Restrito a Administrador, Coordenador e Secretaria.
- Relatórios (`apps/relatorios`): quatro relatórios somente leitura, a
  partir dos mesmos dados da Grade — grade semanal de um professor (em
  todas as turmas que ele leciona), ocupação da carga horária de cada
  professor (com barra de progresso), ocupação de cada ambiente em
  relação à sua capacidade total, e pendências da grade (quais turmas
  ainda têm aulas faltando encaixar, com atalho direto para gerar
  automaticamente). Restrito a Administrador, Coordenador e Secretaria.
- Exportações (`apps/exportacoes`): baixe a grade de uma turma (na tela da
  Grade) ou de um professor (no relatório "Grade por professor") em
  Excel, PDF, Word, PNG ou JPEG — os 5 formatos pedidos na especificação.
  Reaproveita o mesmo grid da tela, então o arquivo baixado é sempre
  idêntico ao que está sendo mostrado. Restrito a Administrador,
  Coordenador e Secretaria.
- API REST (`apps/api`, em `/api/v1/`): Professores, Disciplinas, Turmas,
  Ambientes, Horários, Disponibilidade, Atribuições, Grade e Calendário
  com CRUD completo (via [Django REST Framework](https://www.django-rest-framework.org/));
  Usuários é somente leitura (criar/editar usuário com senha continua
  exclusivo da tela web). Mesmas permissões por papel das telas web, e as
  mesmas regras de conflito da Grade (Módulo 10) e de datas do Calendário
  (Módulo 12) — nada que a tela impede consegue ser criado pela API.
  Autenticação por sessão (faça login pela tela web normalmente antes de
  chamar a API).
- Auditoria (`apps/auditoria`): tela de consulta (`/auditoria/`), restrita
  a Administrador, que mostra quem criou, alterou ou removeu qualquer
  registro do sistema (professor, disciplina, turma, ambiente, horário,
  disponibilidade, atribuição, aula da grade, evento do calendário e
  usuário), além de todo login, logout e tentativa de login que falhou —
  com data/hora, usuário, ação, modelo/objeto afetado e endereço IP.
  Funciona por sinais do Django (`post_save`/`post_delete`), então nenhuma
  tela ou view dos 15 módulos anteriores precisou ser alterada para isso
  passar a ser registrado. Filtros por modelo e por tipo de ação.
  Somente leitura — nem pelo admin do Django dá para editar ou apagar
  um registro de auditoria.
- Backup (`apps/backup`): tela de backup (`/backup/`), restrita a
  Administrador. Um clique gera um dump completo do banco (via `pg_dump`)
  e guarda no histórico; dá para baixar qualquer backup gerado, restaurar
  o banco a partir dele (via `psql`) ou removê-lo. Restaurar é a ação
  mais sensível do sistema — só pede que se digite o nome exato do
  arquivo para confirmar, e fica registrada na Auditoria (Módulo 16) com
  uma ação própria ("Restauração de backup"), tenha dado certo ou não.
  Também vêm dois comandos de terminal para quem quiser agendar via
  cron/Tarefas do Windows: `python manage.py backup_automatico` (gera um
  backup sem precisar de ninguém logado) e
  `python manage.py limpar_backups_antigos` (remove os backups mais
  velhos que `BACKUP_RETENCAO_DIAS`, padrão 30 dias).
- Testes (Módulo 18): além da suíte própria de cada um dos 17 módulos
  anteriores, um teste de integração de ponta a ponta
  (`tests_e2e/test_fluxo_completo.py`) percorre o fluxo real de uma
  escola inteiro: cadastra professor/disciplina/turma/ambiente/horários,
  atribui quem dá o quê, gera a grade automaticamente (OR-Tools), confere
  o resultado na grade visual e no relatório de pendências, exporta em
  Excel, confirma que a API mostra as mesmas aulas, confirma que a
  Auditoria registrou tudo, gera um backup, apaga os dados e restaura —
  provando que os 17 módulos continuam funcionando juntos, não só cada um
  isoladamente. Também tem relatório de cobertura de código (`coverage`)
  e uma pipeline de CI (`.github/workflows/testes.yml`) que roda a suíte
  inteira automaticamente a cada push/pull request, contra um PostgreSQL
  e um Redis de verdade.
- Interface Bootstrap 5, responsiva, com tema claro/escuro. O menu
  lateral é agrupado por assunto (Cadastros, Planejamento,
  Administração) em seções que abrem/fecham — sem isso, a lista de
  telas (quase 20, um item por módulo) ficava comprida demais para
  navegar de relance.
- Banco de dados PostgreSQL (nunca planilhas).
- Testes automatizados (223 testes: 222 nas suítes de cada módulo mais o
  teste de integração de ponta a ponta) cobrindo login, permissões,
  dashboard, professores, disciplinas, turmas, ambientes, horários,
  disponibilidade, as regras de conflito da grade, o algoritmo automático
  de geração, o calendário acadêmico, os relatórios, as exportações, a
  API, a auditoria, o backup/restauração do banco e o fluxo completo
  integrado.
- Estrutura pronta para rodar em Docker Compose (Django + PostgreSQL + Redis).

## Como rodar (recomendado: Docker)

Pré-requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado.

1. Copie `.env.example` para `.env` e ajuste `DJANGO_SECRET_KEY` (qualquer texto
   aleatório longo serve para desenvolvimento).
2. No terminal, dentro da pasta `sigha`, rode:

   ```
   docker compose up --build
   ```

3. Em outro terminal, crie o primeiro usuário administrador:

   ```
   docker compose exec web python manage.py createsuperuser
   ```

   Ao ser perguntado pelo "papel", esse comando ainda não pergunta — depois de
   criado, acesse `/admin/`, abra o usuário criado e defina o campo **Papel**
   como "Administrador".

4. Acesse `http://localhost:8000/usuarios/login/` no navegador.

5. (Opcional) Carregue uma grade de aulas de exemplo para testar o
   sistema com dados prontos, em vez de cadastrar tudo manualmente:

   ```
   docker compose exec web python manage.py carregar_dados_exemplo
   ```

   Veja a seção **Dados de exemplo** mais abaixo para saber o que isso cria.

## Como rodar sem Docker (direto no seu computador)

Requer Python 3.11+ e um PostgreSQL rodando localmente.

```
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # e ajuste DB_HOST=localhost, etc.
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Dados de exemplo

```
python manage.py carregar_dados_exemplo            # carrega
python manage.py carregar_dados_exemplo --limpar   # remove
```

Cria uma grade de aulas completa para testar o sistema sem precisar
cadastrar tudo manualmente — com turmas nas **três etapas da Educação
Básica**, na divisão oficial do MEC/LDB ([saibatecnologias.com.br, "Quais
são as Séries do Ensino Fundamental?"](https://sabertecnologias.com.br/conteudo/quais-sao-as-series-do-ensino-fundamental-guia-completo)):

- **Fundamental I** (Anos Iniciais, 1º ao 5º ano) — turma **3º Ano A**,
  com uma professora regente dando a maior parte das aulas (Português,
  Matemática, Ciências, Geografia, História) e especialistas para Educação
  Física, Inglês, Informática, Arte e Música — o modelo real desta etapa.
- **Fundamental II** (Anos Finais, 6º ao 9º ano) — turmas **6º Ano A** e
  **9º Ano B**, compartilhando os mesmos professores entre si (ex.: o
  professor de Matemática dá aula nas duas), com Língua Portuguesa,
  Matemática, Ciências, Geografia, História, Educação Física, Inglês,
  Informática, Desenho Geométrico, Arte e (só no 9º Ano) Geometria.
- **Ensino Médio** (1º ao 3º ano) — turma **1º Ano A**, com um professor
  especialista por disciplina: Língua Portuguesa, Matemática, Biologia,
  Química, Física, História, Geografia, Filosofia, Sociologia, Arte,
  Educação Física, Inglês, Espanhol e Redação.

O currículo de cada etapa (quantas aulas semanais de cada disciplina) foi
tirado de grades curriculares reais: Fundamental I e II do [Colégio
Fito](https://www.fito.edu.br/arquivos/Ensino-Fundamental.pdf); Ensino
Médio da [Faculdade Itop](https://www.faculdadeitop.edu.br/files/download/20210116160027_grade_curricular_1.2.3_ano_diurno.pdf).

- 31 professores no total, com carga horária compatível com o que cada
  um dá (mais uma folga, como qualquer contrato real).
- 3 ambientes (salas de aula, laboratório de informática, quadra) e 8
  horários (7 aulas de 50 minutos a partir das 07:00 + intervalo — o
  padrão de aula de 50 minutos adotado em 2026 pela rede estadual de SP).
  A 7ª aula é a "folga" da semana: com turmas de currículo cheio (até 30
  aulas semanais), usar exatamente 6 aulas/dia deixaria o algoritmo
  automático sem margem para encaixar tudo sem conflito de professor.
- Algumas disponibilidades de professor marcadas como indisponível (ex.:
  professor de Educação Física não dá a 1ª aula de segunda), para a tela
  de Disponibilidade não ficar "tudo disponível sempre".
- 4 eventos no calendário (2 feriados nacionais, 1 reunião pedagógica, 1
  prova).
- A grade das quatro turmas já **gerada automaticamente** pelo Módulo 11
  (OR-Tools) — 115 aulas (30 + 30 + 30 + 25) encaixadas sem nenhum
  conflito, prontas para ver na Grade, nos Relatórios, exportar ou
  consultar pela API.

O comando é idempotente (rodar de novo sem `--limpar` não duplica nada)
e reversível (`--limpar` remove tudo, exceto os Horários — eles são uma
configuração da escola inteira, não só do exemplo, e é seguro deixá-los).
Todos os registros de exemplo são identificáveis (turmas e ambientes
começam com `[Exemplo]`, professores e disciplinas têm matrícula/sigla
começando com `EX`), então nunca se confundem com dados reais.

## Estrutura de pastas

```
config/            configurações do projeto (settings, urls)
apps/usuarios/      Módulo 1 e 2 — usuários, login, permissões
apps/dashboard/     Módulo 3 — indicadores e gráficos
apps/professores/   Módulo 4 — cadastro de professores
apps/disciplinas/   Módulo 5 — cadastro de disciplinas
apps/turmas/        Módulo 6 — cadastro de turmas
apps/ambientes/     Módulo 7 — cadastro de ambientes
apps/horarios/      Módulo 8 — configuração dos horários da grade
apps/disponibilidade/ Módulo 9 — disponibilidade dos professores
apps/grade/         Módulo 10 — grade de horários (visual + regras de conflito + atribuições)
apps/substituicoes/ Módulo 19 — substituição pontual de professor por data
apps/algoritmo/     Módulo 11 — geração automática da grade (OR-Tools)
apps/calendario/    Módulo 12 — calendário acadêmico (feriados, eventos, provas)
apps/relatorios/    Módulo 13 — relatórios somente leitura (carga horária, ocupação, pendências)
apps/exportacoes/   Módulo 14 — exporta a grade em Excel/PDF/Word/PNG/JPEG
apps/api/           Módulo 15 — API REST (Django REST Framework)
apps/auditoria/     Módulo 16 — auditoria (quem fez o quê, login/logout)
apps/backup/        Módulo 17 — backup e restauração do banco (pg_dump/psql)
tests_e2e/          Módulo 18 — teste de integração de ponta a ponta
templates/          layout base (menu lateral, tema claro/escuro)
static/             CSS e JavaScript do tema
docker-compose.yml  Django + PostgreSQL + Redis
.github/workflows/  CI — roda a suíte inteira a cada push/pull request
executar_testes.py  roda todos os testes + relatório de cobertura, num comando só
```

## Rodando os testes

Um comando só, com relatório de cobertura no final (recomendado):

```
python executar_testes.py
```

Ou diretamente pelo `manage.py`, sem cobertura:

```
python manage.py test apps.usuarios apps.dashboard apps.professores apps.disciplinas apps.turmas apps.ambientes apps.horarios apps.disponibilidade apps.grade apps.algoritmo apps.calendario apps.relatorios apps.exportacoes apps.api apps.auditoria apps.backup tests_e2e.test_fluxo_completo
```

O relatório de cobertura em HTML fica em `htmlcov/index.html` depois de
rodar `python executar_testes.py`.

## Integração contínua (CI)

Todo push e pull request roda a suíte inteira automaticamente (ver
`.github/workflows/testes.yml`), contra um PostgreSQL e um Redis reais
(serviços do próprio job), do mesmo jeito que roda localmente.

## Se você já tinha o projeto rodando (Docker)

O Módulo 17 (Backup) criou tabela nova (`backup_registrobackup`) e mudou
uma opção de campo já existente da Auditoria (nova ação "Restauração de
backup") — depois de atualizar os arquivos, reconstrua a imagem (o
Dockerfile agora também instala `postgresql-client`, necessário para
`pg_dump`/`psql`) e rode as migrações:

```
docker compose down
docker compose up --build
docker compose exec web python manage.py migrate
```

O Módulo 18 (Testes) não mudou nada do banco nem da aplicação em
produção — só adicionou testes, cobertura e CI —, então não precisa de
nenhum passo extra além de atualizar os arquivos.

### Correção: layout quebrado em produção

Se o menu lateral aparecia sobreposto ao conteúdo ou o tema claro/escuro
não funcionava ao rodar via Docker, a causa era: o Gunicorn (usado em
produção) não serve arquivos estáticos por padrão, então o navegador
carregava o Bootstrap (que vem de um CDN externo) mas não conseguia
carregar `theme.css`/`theme.js` — daí o layout bugado. Corrigido com o
[WhiteNoise](https://whitenoise.readthedocs.io/), que faz o próprio
Django/Gunicorn servir esses arquivos, sem precisar de Nginx. Também
foram corrigidas as regras de CSS do menu lateral (posição fixa
explícita) e removido um carregamento duplicado do JavaScript do
Bootstrap na tela de login.

## Todos os módulos da especificação estão prontos

Os 18 módulos previstos (Usuários → Testes) foram implementados um de
cada vez, cada um só começando depois que o anterior estava funcionando
de ponta a ponta — a mesma disciplina usada desde o primeiro módulo
(Usuários e Login). O sistema está completo e testado.
