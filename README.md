# AutoPonto

Repositorio organizado como monorepo do MVP AutoPonto.

## Estrutura

```text
.
├── autoponto-backend/   # API Django/DRF, regras academicas, edge e Interscity
├── autoponto-frontend/  # Painel React/Vite
├── docker-compose.yml   # Orquestracao local/producao simples
└── .env.example         # Exemplo de variaveis para o Compose
```

## Como Rodar Tudo

Copie o ambiente da raiz:

```bash
cp .env.example .env
```

Suba os servicos:

```bash
docker compose up --build
```

URLs:

- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000/api/`
- Health check: `http://localhost:8000/api/health/`

## Documentacao

Backend:

- `autoponto-backend/docs/como-rodar.md`
- `autoponto-backend/docs/explicacao-do-codigo.md`
- `autoponto-backend/docs/diagramas-tcc.md`

Frontend:

- `autoponto-frontend/docs/como-rodar.md`
- `autoponto-frontend/docs/explicacao-do-codigo.md`
- `autoponto-frontend/docs/diagramas-tcc.md`

Tambem ha documentos complementares do backend sobre edge e Interscity em `autoponto-backend/docs/`.
