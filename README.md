# SIGHA — Sistema Inteligente de Gestão de Horários Acadêmicos

Status atual: **Módulo 1 (Usuários) e Módulo 2 (Login) concluídos e testados.**
Os próximos módulos (Dashboard, Professores, Disciplinas...) serão implementados
na ordem definida na especificação, um de cada vez.

## O que já funciona

- Modelo de usuário próprio (`apps/usuarios`), com matrícula, telefone, papel
  (Administrador, Coordenador, Secretaria, Professor, Consulta) e status ativo/inativo.
- Login/logout com proteção contra força bruta (máx. 10 tentativas/minuto por IP),
  CSRF, cookies seguros e bloqueio de usuários inativos.
- Cadastro de usuários (listar, criar, editar, ativar/desativar) — restrito a
  Administrador e Coordenador.
- Interface Bootstrap 5, responsiva, com tema claro/escuro.
- Banco de dados PostgreSQL (nunca planilhas).
- Testes automatizados (8 testes cobrindo login e permissões).
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
config/           configurações do projeto (settings, urls)
apps/usuarios/     Módulo 1 e 2 — usuários, login, permissões
templates/         layout base (menu lateral, tema claro/escuro)
static/            CSS e JavaScript do tema
docker-compose.yml Django + PostgreSQL + Redis
```

## Rodando os testes

```
python manage.py test apps.usuarios
```

## Próximos módulos (na ordem da especificação)

Dashboard → Professores → Disciplinas → Turmas → Ambientes → Horários →
Disponibilidade → Grade → Algoritmo automático (OR-Tools) → Calendário →
Relatórios → Exportações (Excel/PDF/Word/PNG/JPEG) → API → Auditoria → Backup.

Cada módulo só começa depois que o anterior está funcionando de ponta a ponta,
igual foi feito aqui com Usuários e Login.
