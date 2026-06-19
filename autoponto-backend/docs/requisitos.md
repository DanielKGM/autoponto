# Requisitos Do Backend AutoPonto

Este documento traduz o comportamento atual da API em requisitos funcionais e nao funcionais para uso no TCC.

## Requisitos Funcionais

| ID | Requisito | Evidencia No Codigo |
| --- | --- | --- |
| RF-BE-01 | Autenticar usuarios por JWT, mantendo refresh token em cookie `HttpOnly`. | `api/views/autenticacao.py`, `api.ts` no frontend |
| RF-BE-02 | Retornar o usuario autenticado, papel e areas de tela permitidas. | `GET /api/me/`, `_payload_permissoes` em `views/frontend.py` |
| RF-BE-03 | Permitir que aluno consulte apenas suas turmas do periodo ativo. | `GET /api/me/turmas/`, `turmas_do_aluno` |
| RF-BE-04 | Permitir que aluno consulte apenas suas presencas. | `GET /api/me/presencas/`, `presencas_do_aluno` |
| RF-BE-05 | Permitir que aluno cadastre a propria biometria com validacao de imagem e duplicidade facial. | `POST /api/me/biometria/`, `matricular_biometria_aluno` |
| RF-BE-06 | Permitir que professor consulte apenas turmas que ministra; admin consulta todas. | `GET /api/professor/turmas/` |
| RF-BE-07 | Permitir relatorio de presencas por turma e data para professor da turma ou admin. | `RelatorioPresencasTurmaDataView` |
| RF-BE-08 | Permitir resumo de presenca por turma em um periodo. | `RelatorioResumoTurmaView` |
| RF-BE-09 | Permitir historico de presenca de aluno apenas para admin, para o proprio aluno ou para professor que ministra turma daquele aluno. | `_usuario_pode_historico_aluno` em `views/frontend.py` |
| RF-BE-10 | Permitir CRUD administrativo de usuarios sem email obrigatorio, cursos, disciplinas, turmas, matriculas, salas, nos e ESP32. | ViewSets registrados em `api/urls.py` |
| RF-BE-11 | Sincronizar dados academicos e biometricos com o no de borda por `GET /api/edge/pull`. | `montar_payload_pull` |
| RF-BE-12 | Receber eventos de presenca do no por `POST /api/edge/attendance`, com idempotencia por id do evento. | `receber_presencas_borda` |
| RF-BE-13 | Validar presenca somente entre `Aula.inicio` e `Aula.fim` e recusar aulas fechadas/canceladas. | `_receber_evento_borda` |
| RF-BE-14 | Expor mapa publico de ESP32 ativas com recurso IntersCity e coordenadas. | `GET /api/public/mapa/dispositivos/` |
| RF-BE-15 | Permitir que professor da turma ou admin feche manualmente a chamada sem alterar a duracao historica da aula. | `fechar_chamada_aula` |
| RF-BE-16 | Diagnosticar disponibilidade dos microsservicos IntersCity sem depender deles para o fluxo academico. | `GET /api/interscity/diagnostico/` |
| RF-BE-17 | Disponibilizar documentacao OpenAPI/Swagger em /api/schema/ e /api/docs/ quando PUBLIC_API_DOCS=True. | `autoponto/urls.py` |
| RF-BE-18 | Popular ambiente de demonstracao com seed idempotente UFMA/TCC sem matricular alunos automaticamente. | seed_dados_ufma |
| RF-BE-19 | Consultar historico operacional das ESP32 no Data Collector por proxy publico tolerante a falhas. | `GET /api/public/mapa/dispositivos/{id}/historico/` |

## Requisitos Nao Funcionais

| ID | Requisito | Observacao |
| --- | --- | --- |
| RNF-BE-01 | A API deve falhar cedo quando variaveis obrigatorias estiverem ausentes ou vazias. | `env_obrigatoria` em `settings.py` |
| RNF-BE-02 | O banco oficial do MVP deve ser PostgreSQL. | `DATABASES` usa `django.db.backends.postgresql` |
| RNF-BE-03 | Imagens de biometria nao devem ser persistidas; apenas embeddings e metadados seguros. | Servico de biometria |
| RNF-BE-04 | Embeddings faciais nao devem ser expostos em endpoints publicos do frontend. | Serializers/permissoes de biometria |
| RNF-BE-05 | Tokens do no de borda devem expirar e so autenticar endpoints `/api/edge/*`. | `TokenNoBorda`, `EdgeNodeTokenAuthentication` |
| RNF-BE-06 | Falhas do IntersCity nao podem bloquear login, CRUD, presenca, biometria, relatorios ou sync edge. | Cliente IntersCity isolado para diagnostico |
| RNF-BE-07 | A documentacao externa da API deve expor contrato, nao dados; endpoints continuam protegidos por autenticacao/permissao. | `PUBLIC_API_DOCS` controla schema/docs |
| RNF-BE-08 | O contrato com o edge deve manter nomes compativeis com `referencia-edge/autoponto-edgenode/services/edge-app/app/models.py`. | Payloads `salas`, `dispositivos`, `aulas`, `alunos`, `matriculas_aula`, `embeddings_faciais` |
| RNF-BE-09 | O deploy deve funcionar atras do prefixo `/interscity_lh/catalog/autoponto/`. | Compose/Nginx/proxy docs |
| RNF-BE-10 | O MVP deve ser explicavel: modelos enxutos, horarios UFMA tabelados e regras academicas concentradas em services/views. | `HorarioPadraoUFMA`, `services/aulas.py`, `services/relatorios.py` |
