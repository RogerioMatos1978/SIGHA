# SIGHA — Sistema Inteligente de Gestão de Horários Acadêmicos

Status atual: **Módulo 1 (Usuários), Módulo 2 (Login) e Módulo 3 (Dashboard)
concluídos e testados.** Os próximos módulos (Professores, Disciplinas...)
serão implementados na ordem definida na especificação, um de cada vez.

## O que já funciona

- Modelo de usuário próprio (`apps/usuarios`), com matrícula, telefone, papel
  (Administrador, Coordenador, Secretaria, Professor, Consulta) e status ativo/inativo.
- Login/logout com proteção contra força bruta (máx. 10 tentativas/minuto por IP),
  CSRF, cookies seguros e bloqueio de usuários inativos.
- Cadastro de usuários (listar, criar, editar, ativar/desativar) — restrito a
  Administrador e Coordenador.
- Dashboard (`apps/dashboard`) com indicadores de usuários (total, ativos,
  inativos, gráfico por papel) e cartões para os indicadores acadêmicos
  (professores, disciplinas, turmas, ambientes, carga horária, conflitos)
  que aparecem como "Em breve" até os módulos correspondentes existirem.
- Interface Bootstrap 5, responsiva, com tema claro/escuro.
- Banco de dados PostgreSQL (nunca planilhas).
- Testes automatizados (12 testes cobrindo login, permissões e dashboard).
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
templates/          layout base (menu lateral, tema claro/escuro)
static/             CSS e JavaScript do tema
docker-compose.yml  Django + PostgreSQL + Redis
```

## Rodando os testes

```
python manage.py test apps.usuarios apps.dashboard
```

## Se você já tinha o projeto rodando (Docker)

Como não houve nenhum modelo novo neste módulo, não é preciso rodar migração.
Basta reconstruir a imagem e reiniciar:

```
docker compose up --build
```

## Próximos módulos (na ordem da especificação)

Professores → Disciplinas → Turmas → Ambientes → Horários →
Disponibilidade → Grade → Algoritmo automático (OR-Tools) → Calendário →
Relatórios → Exportações (Excel/PDF/Word/PNG/JPEG) → API → Auditoria → Backup.

Cada módulo só começa depois que o anterior está funcionando de ponta a ponta,
igual foi feito aqui com Usuários e Login.
