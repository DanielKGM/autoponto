# AutoPonto

Repositorio organizado como monorepo do MVP AutoPonto.

## Estrutura

```text
.
|-- autoponto-backend/   # API Django/DRF, regras academicas, edge e Interscity
|-- autoponto-frontend/  # Painel React/Vite
|-- docker-compose.yml   # Orquestracao local/producao simples
`-- .env.example         # Exemplo de variaveis para o Compose
```

## Ambiente

Existe uma unica fonte de variaveis de ambiente: `.env` na raiz do repositorio.

- O `docker-compose.yml` le esse arquivo automaticamente.
- O backend carrega esse arquivo em execucao local, sem sobrescrever variaveis ja exportadas no sistema.
- O frontend usa `envDir: ".."` no Vite, entao tambem le o mesmo `.env` da raiz.

Nao ha `.env.example` especifico dentro de `autoponto-backend/` ou `autoponto-frontend/` para evitar divergencia.

## Tecnologias E Justificativas

| Parte | Tecnologia | Uso No Projeto | Justificativa |
| --- | --- | --- | --- |
| Backend | Python 3.13 | Linguagem da API principal | Ecossistema maduro para web, automacao, testes e integracao com bibliotecas de visao computacional. |
| Backend | Django | Base da aplicacao web | Entrega estrutura robusta para modelos, autenticacao, admin, migrations e organizacao de projeto. |
| Backend | Django REST Framework | API REST | Facilita serializers, ViewSets, permissoes e contratos HTTP para frontend, edge e integracoes. |
| Backend | PostgreSQL | Banco de dados unico do sistema | Banco relacional robusto para dominio academico, presencas, relatorios e integridade referencial. |
| Backend | Simple JWT | Autenticacao do frontend | Mantem login por token Bearer simples para aluno, professor e administrador. |
| Backend | OpenCV YuNet/SFace | Geracao de embeddings faciais | Alinha o cadastro biometrico do backend com o reconhecimento usado no edge. |
| Backend | Gunicorn | Servidor WSGI em container | Opcao comum e estavel para servir Django em deploy Linux. |
| Backend | WhiteNoise | Arquivos estaticos do Django | Permite servir estaticos administrativos/coletados no container sem servico extra. |
| Backend | django-cors-headers | CORS para o frontend | Controla origens permitidas quando frontend e backend rodam em portas/dominos diferentes. |
| Frontend | React | Interface web | Componentizacao simples para telas por papel e atualizacao reativa dos dados da API. |
| Frontend | TypeScript | Tipagem do frontend | Reduz erros de contrato entre telas e respostas da API. |
| Frontend | Vite | Build e servidor local | Build rapido, configuracao pequena e boa ergonomia para MVP. |
| Frontend | Nginx | Servir build em container | Entrega arquivos estaticos e faz proxy de `/api/` para o backend no Compose. |
| Infra | Docker Compose | Orquestracao local/deploy simples | Sobe PostgreSQL, backend e frontend com um comando, facilitando demonstracao do TCC. |
| Integracao | Interscity UFMA | Camada IoT opcional | Representa recursos, capacidades, telemetria e comandos sem tornar o AutoPonto dependente da plataforma externa. |

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
- PostgreSQL local: `localhost:5432`

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
