# Explicacao Geral Do Frontend

O frontend e um painel React + Vite para demonstrar o MVP do AutoPonto. Ele nao substitui o admin do Django; ele oferece uma interface operacional para aluno, professor, administrador e tambem uma pagina publica de mapa IoT.

## Estrutura

- `package.json`: scripts e dependencias do projeto.
- `vite.config.ts`: configuracao do servidor Vite.
- `index.html`: ponto de entrada HTML.
- `src/main.tsx`: monta a aplicacao React dentro do elemento `root`.
- `src/app/App.tsx`: define rotas publicas, rotas protegidas e redirecionamentos.
- `src/app/navigation.ts`: calcula destinos e itens de menu conforme permissoes retornadas por `/api/me/`.
- `src/shell/`: layout autenticado, sidebar, header, dropdown de usuario e backdrop responsivo.
- `src/shared/api.ts`: cliente HTTP com JWT, refresh via cookie e tratamento de erros.
- `src/shared/types.ts`: tipos TypeScript usados nas respostas da API.
- `src/shared/ui/`: componentes reutilizaveis como tabela, modal, toast, botoes, graficos e estados vazios.
- `src/shared/domain/`: funcoes de dominio para calendario, status de aula e status do aluno.
- `src/shared/theme/`: alternancia de tema.
- `src/scss/v4/`: estilos SCSS do painel.
- `nginx.conf`: configuracao para servir o build e encaminhar `/api/`.
- `nginx.prod.conf`: configuracao para servir o build no prefixo publico temporario da VM.
- `Dockerfile`: build multi-stage com Node e Nginx.

## Cliente De API

O arquivo `src/shared/api.ts` define:

- `apiFetch`: funcao principal para chamar a API.
- `login`: autentica em `/auth/token/` e carrega `/me/`.
- `tentarRefresh`: tenta renovar o access token quando a API retorna `401`.
- `detalheErro`: converte erros HTTP em mensagens legiveis.
- `logout`: chama `/auth/logout/` e limpa a sessao local mesmo se o cookie ja tiver expirado.

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

As telas ficam separadas por dominio em `src/features/`, enquanto `src/app/App.tsx` define as rotas:

- Publicas: `/`, `/signin`, `/mapa-iot` e `*`.
- Privadas: `/app/aluno`, `/app/calendario`, `/app/aluno/biometria`, `/app/professor`, `/app/admin/academico`, `/app/admin/iot`, `/app/mapa-iot`, `/app/perfil`.
- Detalhes de aulas/turmas: `/app/turmas/:turmaId`, `/app/turmas/:turmaId/aulas/:aulaId` e `/app/aulas/:aulaId`.

### Login

Recebe usuario e senha, chama `login()`, guarda o access token apenas em memoria e deixa o refresh token no cookie `HttpOnly` definido pelo backend.

### Area Do Aluno

Usa:

- `GET /api/me/dashboard-aluno/`
- `GET /api/me/turmas/`
- `GET /api/me/presencas/`
- `GET /api/me/frequencia/`
- `GET /api/me/calendario-aulas/`
- `GET /api/me/biometrias/`
- `POST /api/me/biometria/`
- `DELETE /api/me/biometrias/{id}/`
- `GET /api/me/eventos-reconhecimento/`

Mostra dashboard, aulas de hoje, proximas aulas, frequencia por turma, calendario, detalhe de aula/turma, eventos de reconhecimento e cadastro/revogacao de biometria por upload de imagens.

### Area Do Professor

Usa:

- `GET /api/professor/dashboard/`
- `GET /api/professor/turmas/`
- `GET /api/professor/turmas/{id}/frequencia/`
- `GET /api/turmas/{id}/aula/`
- `GET /api/turmas/{id}/aula/{aula_id}/`
- `GET /api/relatorios/turmas/{id}/presencas/`
- `GET /api/relatorios/turmas/{id}/resumo/`

Permite acompanhar chamadas abertas/pendentes, consultar calendario, abrir detalhe de turma/aula e ver presentes, ausentes, resumo percentual e historico de reconhecimento.

### Area Administrativa

Usa CRUDs do backend e endpoints de relatorio. As paginas atuais sao:

- `features/admin/pages/AdminAcademicoPage.tsx`: usuarios, campus, predios, salas, periodos, cursos, disciplinas, horarios UFMA, turmas, matriculas e vinculos de professor.
- `features/admin/pages/AdminIotPage.tsx`: nos de borda, tokens, ESP32, diagnostico IntersCity e dados de infraestrutura IoT.
- Endpoints CRUD: `/api/usuarios/`, `/api/campi/`, `/api/predios/`, `/api/salas/`, `/api/periodos-letivos/`, `/api/cursos/`, `/api/disciplinas/`, `/api/horarios-padrao-ufma/`, `/api/turmas/`, `/api/matriculas-turma/`, `/api/nos-borda/`, `/api/dispositivos-esp32/`.
- Relatorios e aulas: `/api/relatorios/*`, `/api/aulas/`, `/api/turmas/{id}/aula/`.
- `GET /api/interscity/diagnostico/`: mostra a saude do Collector configurado; a telemetria IntersCity do MVP e publicada pelo edge-node.

O objetivo e demonstrar cadastros academicos completos, geracao de aulas, vinculos, chamadas e monitoramento IoT sem depender do admin do Django.

### Mapa IoT

Usa endpoints publicos:

- `GET /api/public/mapa/nos/`
- `GET /api/public/mapa/dispositivos/{id}/historico/?periodo=2h|1d|7d|recentes`

A pagina agrupa dispositivos por no de borda, usa Leaflet para o mapa, ECharts para graficos e mostra historico do Collector com gaps reais quando faltam amostras. O PIR e normalizado pelo backend como histograma.

## Estilo

O CSS usa uma interface operacional: tabelas, formularios e paineis compactos. A ideia e parecer uma ferramenta de uso academico, nao uma landing page.

## Limitacoes Do MVP

- As telas administrativas cobrem os cadastros necessarios ao MVP, mas continuam focadas no fluxo de TCC, nao em um ERP academico completo.
- Nao usa React Query; os carregamentos ficam nas paginas e componentes atuais para manter o projeto menor.
- O access token fica somente em memoria no React; o refresh token fica em cookie `HttpOnly`, reduzindo exposicao em caso de XSS.

## Estrutura Atual Do Frontend

O frontend foi separado de forma minimalista para continuar facil de estudar:

- `src/app/`: rotas, protecao por area, redirecionamento inicial, basename e testes de navegacao.
- `src/shell/`: layout autenticado.
- `src/features/auth/`: login e pagina 404.
- `src/features/aluno/`: dashboard e cadastro/revogacao de biometria.
- `src/features/calendario/`: calendario mensal e modal do dia.
- `src/features/aulas/`: detalhe de turma/aula para aluno e professor.
- `src/features/professor/`: dashboard do professor.
- `src/features/admin/`: paginas academica e IoT, mais `AdminResourceManager` compartilhado.
- `src/features/mapa/`: mapa publico/embutido de nos, dispositivos e telemetria.
- `src/features/perfil/`: dados da conta, biometria e eventos do aluno.
- `src/shared/`: API, sessao, tipos, UI, dominio, tema e assets.
