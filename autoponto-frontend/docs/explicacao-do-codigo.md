# Explicacao Geral Do Frontend

O frontend e um painel React + Vite para demonstrar o MVP do AutoPonto. Ele nao substitui o admin do Django; ele oferece uma interface simples para os tres papeis do sistema: aluno, professor e administrador.

## Estrutura

- `package.json`: scripts e dependencias do projeto.
- `vite.config.ts`: configuracao do servidor Vite.
- `index.html`: ponto de entrada HTML.
- `src/main.tsx`: monta a aplicacao React dentro do elemento `root`.
- `src/App.tsx`: concentra as telas do MVP.
- `src/api.ts`: cliente HTTP com JWT, refresh simples e tratamento de erros.
- `src/types.ts`: tipos TypeScript usados nas respostas da API.
- `src/styles.css`: estilo visual do painel.
- `nginx.conf`: configuracao para servir o build e encaminhar `/api/`.
- `Dockerfile`: build multi-stage com Node e Nginx.

## Cliente De API

O arquivo `src/api.ts` define:

- `apiFetch`: funcao principal para chamar a API.
- `login`: autentica em `/auth/token/` e carrega `/me/`.
- `tentarRefresh`: tenta renovar o access token quando a API retorna `401`.
- `detalheErro`: converte erros HTTP em mensagens legiveis.

A URL base vem de:

```env
VITE_API_URL
```

O Vite usa `envDir: ".."`, portanto essa variavel deve ficar no `.env` unico da raiz do repositorio. O mesmo valor `VITE_API_URL=/api` funciona no desenvolvimento local porque o servidor Vite tem proxy para `http://localhost:8000`, e tambem funciona no Docker porque o Nginx encaminha `/api/` para o backend.

## Telas

Todas as telas estao em `src/App.tsx` para manter o MVP pequeno e facil de explicar.

### Login

Recebe usuario e senha, chama `login()` e salva os tokens no `sessionStorage`.

### Painel Do Aluno

Usa:

- `GET /api/me/turmas/`
- `GET /api/me/presencas/`
- `POST /api/me/biometria/`

Mostra turmas do periodo ativo, presencas registradas e cadastro biometrico por upload de imagem.

### Painel Do Professor

Usa:

- `GET /api/professor/turmas/`
- `GET /api/relatorios/turmas/{id}/presencas/`
- `GET /api/relatorios/turmas/{id}/resumo/`

Permite selecionar turma/data e ver presentes, ausentes e resumo percentual.

### Painel Administrativo

Usa CRUDs do backend e endpoints de relatorio:

- `POST /api/usuarios/`
- `POST /api/matriculas-turma/`
- `PATCH /api/turmas/{id}/`
- `POST /api/perfis-biometricos/matricular/`
- `GET /api/interscity/diagnostico/`

O objetivo e demonstrar cadastro basico, vinculos academicos e monitoramento da integracao IoT.

## Estilo

O CSS usa uma interface operacional: tabelas, formularios e paineis compactos. A ideia e parecer uma ferramenta de uso academico, nao uma landing page.

## Limitacoes Do MVP

- As telas administrativas sao simples e nao cobrem todos os campos de todos os cadastros.
- Nao usa React Query ou roteamento por URL para manter o projeto menor.
- O token fica em `sessionStorage`, suficiente para demonstracao, mas uma versao de producao deveria avaliar cookies httpOnly.
