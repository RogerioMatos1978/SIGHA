# SIGHA — Sistema Inteligente de Gestão de Horários Acadêmicos

Status atual: **Módulos 1 a 7 concluídos e testados** — Usuários, Login,
Dashboard, Professores, Disciplinas, Turmas e Ambientes. Os próximos módulos
(Horários, Disponibilidade...) serão implementados na ordem definida na
especificação, um de cada vez.

## O que já funciona

- Modelo de usuário próprio (`apps/usuarios`), com matrícula, telefone, papel
  (Administrador, Coordenador, Secretaria, Professor, Consulta) e status ativo/inativo.
- Login/logout com proteção contra força bruta (máx. 10 tentativas/minuto por IP),
  CSRF, cookies seguros e bloqueio de usuários inativos.
- Cadastro de usuários (listar, criar, editar, ativar/desativar) — restrito a
  Administrador e Coordenador.
- Dashboard (`apps/dashboard`) com indicadores de usuários (total, ativos,
  inativos, gráfico por papel) e cartões para os indicadores acadêmicos
  (carga horária, horários livres, conflitos) que aparecem como "Em breve"
  até o módulo de Grade existir — Professores, Disciplinas, Turmas e
  Ambientes já mostram a contagem real.
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
  Todos restritos a Administrador, Coordenador e Secretaria.
- Interface Bootstrap 5, responsiva, com tema claro/escuro.
- Banco de dados PostgreSQL (nunca planilhas).
- Testes automatizados (42 testes cobrindo login, permissões, dashboard,
  professores, disciplinas, turmas e ambientes).
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
templates/          layout base (menu lateral, tema claro/escuro)
static/             CSS e JavaScript do tema
docker-compose.yml  Django + PostgreSQL + Redis
```

## Rodando os testes

```
python manage.py test apps.usuarios apps.dashboard apps.professores apps.disciplinas apps.turmas apps.ambientes
```

## Se você já tinha o projeto rodando (Docker)

Este módulo criou uma tabela nova (`ambientes_ambiente`), então é
preciso migrar depois de atualizar:

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

Horários → Disponibilidade → Grade → Algoritmo automático (OR-Tools) →
Calendário → Relatórios → Exportações (Excel/PDF/Word/PNG/JPEG) → API →
Auditoria → Backup.

Cada módulo só começa depois que o anterior está funcionando de ponta a ponta,
igual foi feito aqui com Usuários e Login.
