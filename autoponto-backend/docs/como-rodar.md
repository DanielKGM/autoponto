# Como Rodar O Backend

Este documento explica como rodar apenas a API Django/DRF do AutoPonto.

## Requisitos

- Python 3.13.
- Uma venv Python.
- SQLite para desenvolvimento local simples.
- Postgres para o deploy com Docker Compose.

## Ambiente Local

Entre na pasta do backend:

```bash
cd autoponto-backend
```

Crie o arquivo de ambiente:

```bash
cp .env.example .env
```

Instale dependencias:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

No Windows PowerShell, se a venv ja existir na raiz do repositorio, tambem pode usar:

```powershell
..\.venv\Scripts\python.exe autoponto\manage.py test api
```

## Banco E Servidor

Aplicar migrations:

```bash
python autoponto/manage.py migrate
```

Carregar dados de exemplo da UFMA:

```bash
python autoponto/manage.py seed_dados_ufma
```

Subir servidor local:

```bash
python autoponto/manage.py runserver 0.0.0.0:8000
```

URLs principais:

- API: `http://localhost:8000/api/`
- Health check: `http://localhost:8000/api/health/`
- Readiness: `http://localhost:8000/api/ready/`

## Testes

```bash
python autoponto/manage.py test api
python autoponto/manage.py makemigrations --check --dry-run
```

## Docker

O Dockerfile do backend fica em `autoponto-backend/Dockerfile`, mas o Compose fica na raiz do repositorio.

Subir tudo:

```bash
cd ..
docker compose up --build
```

Servicos:

- Backend: `http://localhost:8000/api/`
- Frontend: `http://localhost:8080`
- Banco: container `db`

## Variaveis Importantes

- `DJANGO_SECRET_KEY`: segredo do Django.
- `DJANGO_DEBUG`: `True` em desenvolvimento, `False` em deploy.
- `DATABASE_*` ou `DATABASE_URL`: configuracao do banco.
- `CORS_ALLOWED_ORIGINS`: origens aceitas para o frontend.
- `INTERSCITY_ENABLED`: ativa/desativa integracao externa.
- `FACE_DUPLICATE_THRESHOLD`: limite para bloquear rosto duplicado.
- `EDGE_SYNC_DAYS_BACK` e `EDGE_SYNC_DAYS_FORWARD`: janela de sincronizacao do Raspberry.
