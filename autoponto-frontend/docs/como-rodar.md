# Como Rodar O Frontend

Este documento explica como rodar apenas o painel React/Vite do AutoPonto.

## Requisitos

- Node.js 22 ou superior.
- Backend AutoPonto rodando em `http://localhost:8000/api`.

## Ambiente Local

Na raiz do repositorio, crie o arquivo de ambiente:

```bash
cp .env.example .env
```

Preencha os valores sensiveis vazios antes de rodar o Compose ou o backend. O Vite esta configurado com `envDir: ".."`, entao ele le esse `.env` da raiz. Depois entre na pasta do frontend:

```bash
cd autoponto-frontend
```

Instale dependencias:

```bash
npm install
```

Suba o Vite:

```bash
npm run dev
```

URL padrao:

- Frontend local: `http://localhost:5173`

## Variavel De API

```env
VITE_API_URL=/api
VITE_BASE_PATH=/
```

Com `npm run dev`, o Vite encaminha `/api` para `http://localhost:8000`. No Docker Compose de desenvolvimento, o Nginx do frontend encaminha `/api/` para o backend.

Para o deploy provisorio na VM, o build usa:

```env
VITE_BASE_PATH=/interscity_lh/catalog/autoponto/
VITE_API_URL=/interscity_lh/catalog/autoponto/api
```

Esse prefixo faz os assets do React e as chamadas da API funcionarem sob `https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/catalog/autoponto/`.

## Build

```bash
npm run build
```

O resultado fica em `dist/`.

## Docker

O Dockerfile do frontend fica em `autoponto-frontend/Dockerfile`, mas o Compose fica na raiz do repositorio.

Subir tudo em desenvolvimento:

```bash
cd ..
docker compose up --build
```

Se a porta `8080` estiver ocupada, altere `FRONTEND_PORT` no `.env` da raiz e use a nova porta no navegador.

Servicos:

- Frontend: `http://localhost:${FRONTEND_PORT}`; no exemplo padrao, `http://localhost:8080`
- Backend: `http://localhost:8000/api/`

## Producao Provisoria Na VM

Use o Compose de producao na raiz:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

O container frontend fica publicado apenas em `127.0.0.1:8088:80`. O arquivo `nginx.prod.conf` serve o React no prefixo `/interscity_lh/catalog/autoponto/` e encaminha `/interscity_lh/catalog/autoponto/api/` para o backend interno.

Como o Apache da VM pode remover o prefixo antes de chegar ao container, o mesmo Nginx tambem encaminha `/api/` para o backend. Assim, `curl -i http://127.0.0.1:8088/api/health/` deve responder pelo Django em producao.

## Login

O login usa JWT:

- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/logout/`
- `GET /api/me/`

O access token fica apenas em memoria no React. O refresh token fica em cookie `HttpOnly`, definido pelo backend, e por isso as chamadas usam `credentials: include`.
