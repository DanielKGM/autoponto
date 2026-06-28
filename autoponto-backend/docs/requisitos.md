# Requisitos Do Backend AutoPonto

Este documento traduz o comportamento atual da API em requisitos funcionais e nao funcionais para uso no TCC.

## Requisitos Funcionais

| ID | Requisito | Evidencia No Codigo |
| --- | --- | --- |
| RF-BE-01 | Autenticar usuarios por JWT, mantendo refresh token em cookie `HttpOnly`. | `api/views/autenticacao.py`, `shared/api.ts` no frontend |
| RF-BE-02 | Retornar o usuario autenticado, papel e areas de tela permitidas. | `GET /api/me/`, `_payload_permissoes` em `views/frontend.py` |
| RF-BE-03 | Permitir que aluno consulte apenas suas turmas do periodo ativo. | `GET /api/me/turmas/`, `turmas_do_aluno` |
| RF-BE-04 | Permitir que aluno consulte apenas suas presencas. | `GET /api/me/presencas/`, `presencas_do_aluno` |
| RF-BE-05 | Permitir que aluno cadastre a propria biometria com validacao de imagem e duplicidade facial. | `POST /api/me/biometria/`, `matricular_biometria_aluno` |
| RF-BE-06 | Permitir que aluno liste e revogue suas proprias biometrias. | `GET /api/me/biometrias/`, `DELETE /api/me/biometrias/{id}/` |
| RF-BE-07 | Permitir que professor consulte apenas turmas que ministra; admin consulta todas. | `GET /api/professor/turmas/` |
| RF-BE-08 | Permitir relatorio de presencas por turma e data para professor da turma ou admin. | `RelatorioPresencasTurmaDataView` |
| RF-BE-09 | Permitir resumo de presenca por turma em um periodo. | `RelatorioResumoTurmaView` |
| RF-BE-10 | Permitir historico de presenca de aluno apenas para admin, para o proprio aluno ou para professor que ministra turma daquele aluno. | `_usuario_pode_historico_aluno` em `views/frontend.py` |
| RF-BE-11 | Permitir CRUD administrativo de usuarios sem email obrigatorio, cursos, disciplinas, turmas, matriculas, salas, nos e ESP32. | ViewSets registrados em `api/urls.py` |
| RF-BE-12 | Sincronizar dados academicos e biometricos das aulas do dia com o no de borda por `GET /api/edge/pull`. | `montar_payload_pull` |
| RF-BE-13 | Receber eventos de presenca do no por `POST /api/edge/attendance`, com idempotencia por id do evento. | `receber_presencas_borda` |
| RF-BE-14 | Validar presenca somente no intervalo `Aula.inicio <= reconhecido_em < Aula.fim` e recusar aulas fechadas/canceladas. | `_receber_evento_borda` |
| RF-BE-15 | Expor mapa publico de nos de borda ativos com coordenadas e ESP32 ativas. | `GET /api/public/mapa/nos/` |
| RF-BE-16 | Permitir que professor da turma ou admin feche manualmente a chamada sem alterar a duracao historica da aula. | `fechar_chamada_aula` |
| RF-BE-17 | Diagnosticar disponibilidade do Collector IntersCity sem depender dele para o fluxo academico. | `GET /api/interscity/diagnostico/` |
| RF-BE-18 | Disponibilizar documentacao OpenAPI/Swagger em /api/schema/ e /api/docs/ quando PUBLIC_API_DOCS=True. | `autoponto/urls.py` |
| RF-BE-19 | Popular ambiente de demonstracao com seed idempotente UFMA/TCC sem matricular alunos automaticamente. | seed_dados_ufma |
| RF-BE-20 | Consultar historico operacional das ESP32 no Data Collector por proxy publico tolerante a falhas. | `GET /api/public/mapa/dispositivos/{id}/historico/?periodo=...` |
| RF-BE-21 | Calcular status de aula de forma derivada para calendario, relatorios, filtros e sync edge. | `api/selectors/aulas.py` |

## Requisitos Nao Funcionais

| ID | Requisito | Observacao |
| --- | --- | --- |
| RNF-BE-01 | A API deve falhar cedo quando variaveis obrigatorias estiverem ausentes ou vazias. | `env_obrigatoria` em `settings.py` |
| RNF-BE-02 | O banco oficial do MVP deve ser PostgreSQL. | `DATABASES` usa `django.db.backends.postgresql` |
| RNF-BE-03 | Imagens de biometria nao devem ser persistidas; apenas embeddings e metadados seguros. | Servico de biometria |
| RNF-BE-04 | Embeddings faciais nao devem ser expostos em endpoints publicos do frontend e devem ficar criptografados em repouso. | Serializers/permissoes/crypto de biometria |
| RNF-BE-05 | Tokens do no de borda devem expirar e so autenticar endpoints `/api/edge/*`. | `TokenNoBorda`, `EdgeNodeTokenAuthentication` |
| RNF-BE-06 | Falhas do IntersCity/Collector nao podem bloquear login, CRUD, presenca, biometria, relatorios ou sync edge. | Cliente IntersCity isolado para diagnostico e mapa |
| RNF-BE-07 | A documentacao externa da API deve expor contrato, nao dados; endpoints continuam protegidos por autenticacao/permissao. | `PUBLIC_API_DOCS` controla schema/docs |
| RNF-BE-08 | O contrato com o edge deve entregar um snapshot autoritativo pronto para Redis, sem entidades completas ou incremental. | `cache_redis` com `dispositivos_por_codigo`, `aulas_por_sala`, `alunos_por_aula`, `alunos_por_id`, `embeddings_faciais` |
| RNF-BE-09 | O deploy deve funcionar atras do prefixo `/interscity_lh/catalog/autoponto/`. | Compose/Nginx/proxy docs |
| RNF-BE-10 | O MVP deve ser explicavel: modelos enxutos, horarios UFMA tabelados, aulas materializadas e status derivado sem cron. | `HorarioPadraoUFMA`, `Aula`, `selectors/aulas.py`, `services/aulas.py`, `services/relatorios.py` |
| RNF-BE-11 | Validacao de duplicidade facial deve usar cache Redis configuravel. | `FACE_EMBEDDING_CACHE_URL`, `services/cache_biometria.py` |
