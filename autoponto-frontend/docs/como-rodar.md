# Como Rodar O Frontend

Este documento explica como rodar apenas o painel React/Vite do AutoPonto.

## Requisitos

- Node.js 22 ou superior.
- Backend AutoPonto rodando em `http://localhost:8000/api`.

## Ambiente Local

Crie o arquivo de ambiente na raiz do repositorio:

```bash
cp .env.example .env
```

O Vite esta configurado com `envDir: ".."`, entao ele le esse `.env` da raiz. Depois entre na pasta do frontend:

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
```

Com `npm run dev`, o Vite encaminha `/api` para `http://localhost:8000`. No Docker Compose, o Nginx do frontend encaminha `/api/` para o backend.

## Build

```bash
npm run build
```

O resultado fica em `dist/`.

## Docker

O Dockerfile do frontend fica em `autoponto-frontend/Dockerfile`, mas o Compose fica na raiz do repositorio.

Subir tudo:

```bash
cd ..
docker compose up --build
```

Servicos:

- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000/api/`

## Login

O login usa JWT:

- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`
- `GET /api/me/`

O token fica em `sessionStorage` para simplificar o MVP.
