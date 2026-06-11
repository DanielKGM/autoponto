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
- `nginx.prod.conf`: configuracao para servir o build no prefixo publico temporario da VM.
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
VITE_BASE_PATH
```

O Vite usa `envDir: ".."`, portanto essas variaveis devem ficar no arquivo de ambiente da raiz. Em desenvolvimento, use:

```env
VITE_API_URL=/api
VITE_BASE_PATH=/
```

Na producao provisoria da VM, use:

```env
VITE_API_URL=/interscity_lh/catalog/autoponto/api
VITE_BASE_PATH=/interscity_lh/catalog/autoponto/
```

`VITE_API_URL` define para onde o cliente `fetch` envia requests. `VITE_BASE_PATH` define o prefixo dos assets gerados pelo Vite, evitando quebra de CSS/JS quando o app roda em subcaminho.

## Nginx

No desenvolvimento em container, `nginx.conf` serve o build na raiz e encaminha `/api/` para `backend:8000`.

Na VM, `nginx.prod.conf` serve o app em `/interscity_lh/catalog/autoponto/` e encaminha `/interscity_lh/catalog/autoponto/api/` para `http://backend:8000/api/`. Como o Apache externo pode entregar ao container o caminho ja sem prefixo, o Nginx tambem encaminha `/api/` para o backend. Isso evita 404 no login quando a requisicao publica `/interscity_lh/catalog/autoponto/api/auth/token/` chega internamente como `/api/auth/token/`. O arquivo tambem sobrescreve `X-Forwarded-Host` para impedir `400 Bad Request` HTML causado por host encaminhado de forma inesperada pelo Apache.

## Telas

Todas as telas estao em `src/App.tsx` para manter o MVP pequeno e facil de explicar.

### Login

Recebe usuario e senha, chama `login()`, guarda o access token apenas em memoria e deixa o refresh token no cookie `HttpOnly` definido pelo backend.

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
- O access token fica somente em memoria no React; o refresh token fica em cookie `HttpOnly`, reduzindo exposicao em caso de XSS.
