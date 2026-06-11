# AutoPonto

Repositorio organizado como monorepo do MVP AutoPonto.

## Estrutura

```text
.
|-- autoponto-backend/   # API Django/DRF, regras academicas, edge e Interscity
|-- autoponto-frontend/  # Painel React/Vite
|-- docker-compose.yml   # Orquestracao de desenvolvimento local
|-- docker-compose.prod.yml # Deploy provisorio na VM da faculdade
`-- .env.example         # Exemplo de variaveis para o Compose
```

## Ambiente

Existe uma unica fonte de variaveis de ambiente: `.env` na raiz do repositorio.

- O `docker-compose.yml` le esse arquivo automaticamente.
- O backend carrega esse arquivo em execucao local, sem sobrescrever variaveis ja exportadas no sistema.
- O frontend usa `envDir: ".."` no Vite, entao tambem le o mesmo `.env` da raiz.
- O Compose nao define valores fallback para configuracao de aplicacao; se uma variavel obrigatoria faltar, a subida deve falhar.

Nao ha `.env.example` especifico dentro de `autoponto-backend/` ou `autoponto-frontend/` para evitar divergencia.

Para producao provisoria na VM da faculdade, use `.env.prod` baseado em `.env.prod.example`. Esse arquivo real tambem nao deve ser versionado.

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

### Desenvolvimento

Copie o ambiente da raiz:

```bash
cp .env.example .env
```

Preencha os valores sensiveis que aparecem vazios, como `DJANGO_SECRET_KEY` e `DATABASE_PASSWORD`. O Compose e o backend devem falhar se uma variavel obrigatoria nao estiver configurada.

Para usar cadastro biometrico real, baixe os modelos ONNX em `autoponto-backend/autoponto/data/models/` antes de subir o backend. Eles nao sao versionados:

```bash
mkdir -p autoponto-backend/autoponto/data/models
wget https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx -O autoponto-backend/autoponto/data/models/face_detection_yunet.onnx
wget https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx -O autoponto-backend/autoponto/data/models/face_recognition_sface.onnx
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

### Producao Provisoria Na VM

O deploy temporario usa a URL publica:

```text
https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/catalog/autoponto/
```

Fluxo esperado:

```text
usuario
  -> cidadesinteligentes.lsdi.ufma.br/interscity_lh/catalog/autoponto/
  -> Apache da VM
  -> 127.0.0.1:8088
  -> container frontend
  -> backend interno
  -> PostgreSQL interno
```

Na VM, crie o ambiente real:

```bash
cp .env.prod.example .env.prod
```

Preencha `DJANGO_SECRET_KEY`, `DATABASE_PASSWORD` e demais valores reais. Depois suba a stack de producao:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

No Compose de producao, somente o frontend publica porta local em `127.0.0.1:8088`; backend e PostgreSQL ficam privados na rede Docker.

O build do React usa o prefixo publico completo, mas o Apache da VM pode remover esse prefixo antes de encaminhar para `127.0.0.1:8088`. Por isso o Nginx do frontend aceita tanto `/interscity_lh/catalog/autoponto/api/` quanto `/api/` e encaminha ambos para o backend interno. Para diagnostico na VM, `curl -i http://127.0.0.1:8088/api/health/` deve chegar ao Django.

Criar administrador inicial em producao:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec backend python /app/autoponto/manage.py createsuperuser
```

Qualquer automacao SSH, `git pull` ou rotina operacional de deploy deve ficar na VM ou fora deste repositorio.

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
