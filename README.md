# SIGHA — Sistema Inteligente de Gestão de Horários Acadêmicos

Status atual: **Módulos 1 a 14 concluídos e testados** — Usuários, Login,
Dashboard, Professores, Disciplinas, Turmas, Ambientes, Horários,
Disponibilidade, Grade, Algoritmo automático (OR-Tools), Calendário,
Relatórios e Exportações. Os próximos módulos (API, Auditoria...) serão
implementados na ordem definida na especificação, um de cada vez.

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
  telefone, carga horária semanal, ativo/inativo.
- Cadastro de disciplinas (`apps/disciplinas`): nome, sigla (normalizada
  em maiúscula automaticamente), quantidade de aulas por semana, ativo/inativo.
- Cadastro de turmas (`apps/turmas`): nome, série, turno (Matutino,
  Vespertino, Noturno, Integral), ativo/inativo — mesma turma pode existir
  em turnos diferentes, mas não duplicada no mesmo turno.
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
  que o Módulo 11 usa para gerar a grade sozinho.
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
- Interface Bootstrap 5, responsiva, com tema claro/escuro.
- Banco de dados PostgreSQL (nunca planilhas).
- Testes automatizados (140 testes cobrindo login, permissões, dashboard,
  professores, disciplinas, turmas, ambientes, horários, disponibilidade,
  as regras de conflito da grade, o algoritmo automático de geração, o
  calendário acadêmico, os relatórios e as exportações).
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
apps/algoritmo/     Módulo 11 — geração automática da grade (OR-Tools)
apps/calendario/    Módulo 12 — calendário acadêmico (feriados, eventos, provas)
apps/relatorios/    Módulo 13 — relatórios somente leitura (carga horária, ocupação, pendências)
apps/exportacoes/   Módulo 14 — exporta a grade em Excel/PDF/Word/PNG/JPEG
templates/          layout base (menu lateral, tema claro/escuro)
static/             CSS e JavaScript do tema
docker-compose.yml  Django + PostgreSQL + Redis
```

## Rodando os testes

```
python manage.py test apps.usuarios apps.dashboard apps.professores apps.disciplinas apps.turmas apps.ambientes apps.horarios apps.disponibilidade apps.grade apps.algoritmo apps.calendario apps.relatorios apps.exportacoes
```

## Se você já tinha o projeto rodando (Docker)

Este módulo (Exportações) não criou tabela nova, mas adicionou 4
dependências Python novas (`openpyxl`, `reportlab`, `python-docx`,
`Pillow`) e um pacote de sistema novo (`fonts-dejavu-core`, usado para
desenhar texto legível nas imagens PNG/JPEG) — é preciso reconstruir a
imagem:

```
docker compose down
docker compose up --build
```

O último módulo que exigiu migração de banco foi o Calendário
(`calendario_evento`):

```
docker compose down
docker compose up --build
docker compose exec web python manage.py migrate
```

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

## Próximos módulos (na ordem da especificação)

API → Auditoria → Backup.

Cada módulo só começa depois que o anterior está funcionando de ponta a ponta,
igual foi feito aqui com Usuários e Login.
