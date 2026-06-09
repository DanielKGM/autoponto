# Como Rodar O Backend

Este documento explica como rodar apenas a API Django/DRF do AutoPonto.

## Requisitos

- Python 3.13.
- Uma venv Python.
- PostgreSQL para desenvolvimento local, testes e deploy.

## Ambiente Local

Na raiz do repositorio, crie o arquivo de ambiente:

```bash
cp .env.example .env
```

Preencha os valores sensiveis que aparecem vazios no exemplo, principalmente `DJANGO_SECRET_KEY` e `DATABASE_PASSWORD`. O backend falha ao iniciar se uma variavel obrigatoria estiver ausente ou vazia. Depois entre na pasta do backend:

```bash
cd autoponto-backend
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

O backend usa PostgreSQL como unico banco suportado. Para desenvolvimento local, a forma mais simples e subir o servico `db` do Compose:

```bash
cd ..
docker compose up -d db
cd autoponto-backend
```

O `.env.example` da raiz usa `DATABASE_HOST=localhost`, porque fora do Docker o backend acessa o Postgres pela porta publicada `5432`. Dentro do Compose, o `docker-compose.yml` injeta `DATABASE_HOST=db` apenas no container do backend.

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

Subir tudo em desenvolvimento:

```bash
cd ..
docker compose up --build
```

Servicos:

- Backend: `http://localhost:8000/api/`
- Frontend: `http://localhost:8080`
- Banco: container `db`

## Producao Provisoria Na VM

Na VM `192.168.10.104`, o AutoPonto deve ficar atras da rota publica:

```text
https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/catalog/autoponto/
```

O Apache da VM encaminha a rota para `127.0.0.1:8088`, onde o container frontend fica exposto. Backend e PostgreSQL nao publicam portas no Compose de producao.

Prepare o ambiente real na VM:

```bash
cp .env.prod.example .env.prod
```

Valores importantes para producao:

```env
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=cidadesinteligentes.lsdi.ufma.br,192.168.10.104,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://cidadesinteligentes.lsdi.ufma.br
DATABASE_HOST=db
DATABASE_PORT=5432
VITE_BASE_PATH=/interscity_lh/catalog/autoponto/
VITE_API_URL=/interscity_lh/catalog/autoponto/api
```

Subir a stack:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

Criar administrador inicial:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec backend python /app/autoponto/manage.py createsuperuser
```

Scripts de `git pull`, SSH ou automacao de deploy devem ser mantidos na VM ou fora deste repositorio.

## Variaveis Importantes

- `DJANGO_SECRET_KEY`: segredo do Django.
- `DJANGO_DEBUG`: `True` em desenvolvimento, `False` em deploy.
- `DATABASE_*`: configuracao PostgreSQL; `DATABASE_URL` nao e usado neste MVP.
- `CORS_ALLOWED_ORIGINS`: origens aceitas para o frontend.
- `INTERSCITY_ENABLED`: ativa/desativa integracao externa.
- `INTERSCITY_BASE_URL` e `INTERSCITY_*_PATH`: base da instancia Interscity e path de cada microsservico.
- `FACE_DUPLICATE_THRESHOLD`: limite para bloquear rosto duplicado.
- `EDGE_SYNC_DAYS_BACK` e `EDGE_SYNC_DAYS_FORWARD`: janela de sincronizacao do Raspberry.
