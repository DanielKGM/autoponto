# Evidencias De Codigo E Metricas Para O TCC

Este documento mapeia as partes do codigo do AutoPonto que podem ser citadas em
Metodologia, Desenvolvimento do Prototipo e Analise dos Resultados. Os caminhos
apontam para codigo-fonte, nao para dados reais.

## 1. Partes Do Codigo Por Tema

| Tema | Arquivos principais | O que evidenciam no TCC |
|---|---|---|
| Modelagem academica | `autoponto-backend/autoponto/api/models/academico.py`; `autoponto-backend/autoponto/api/views/academico.py`; `autoponto-backend/autoponto/api/serializers/academico.py` | Campus, predios, salas, periodos letivos, cursos, disciplinas, turmas, matriculas e horarios padrao UFMA. |
| Alunos | `autoponto-backend/autoponto/api/models/identidade.py`; `autoponto-backend/autoponto/api/models/academico.py`; `autoponto-backend/autoponto/api/services/relatorios.py`; `autoponto-frontend/src/features/aluno/` | Papel `ALUNO`, matricula em turma, dashboard discente, biometria propria e frequencia. |
| Professores | `autoponto-backend/autoponto/api/models/identidade.py`; `autoponto-backend/autoponto/api/models/academico.py`; `autoponto-backend/autoponto/api/views/frontend.py`; `autoponto-frontend/src/features/professor/` | Papel `PROFESSOR`, turmas ministradas, dashboard de chamadas e acesso a relatorios. |
| Turmas | `autoponto-backend/autoponto/api/models/academico.py`; `autoponto-backend/autoponto/api/services/aulas.py`; `autoponto-backend/autoponto/api/services/relatorios.py`; `autoponto-frontend/src/features/admin/pages/AdminAcademicoPage.tsx` | Associacao entre periodo, disciplina, codigo, professores, alunos e horarios. |
| Aulas | `autoponto-backend/autoponto/api/models/presencas.py`; `autoponto-backend/autoponto/api/selectors/aulas.py`; `autoponto-backend/autoponto/api/views/presencas.py`; `autoponto-frontend/src/features/calendario/`; `autoponto-frontend/src/features/aulas/` | Aula materializada por turma, sala, horario, data, janela de inicio/fim e status derivado. |
| Dispositivos e nos | `autoponto-backend/autoponto/api/models/dispositivos.py`; `autoponto-backend/autoponto/api/views/dispositivos.py`; `autoponto-frontend/src/features/admin/pages/AdminIotPage.tsx`; `autoponto-frontend/src/features/mapa/pages/PublicMapPage.tsx` | No de borda, token do no, ESP32, sala associada, coordenadas do no e UUID InterSCity. |
| Cadastro biometrico | `autoponto-backend/autoponto/api/models/biometria.py`; `autoponto-backend/autoponto/api/services/biometria.py`; `autoponto-backend/autoponto/api/views/frontend.py`; `autoponto-frontend/src/features/aluno/pages/StudentBiometricsPage.tsx` | Validacao das capturas, geracao de embedding, verificacao de duplicidade, revogacao anterior e criacao de novo embedding ativo. |
| Criptografia de embeddings | `autoponto-backend/autoponto/api/services/crypto_biometria.py`; `autoponto-backend/autoponto/api/services/sincronizacao_borda.py` | Uso de Fernet para criptografar/descriptografar vetores e entregar ciphertext ao EdgeNode. |
| Cache Redis | `autoponto-backend/autoponto/api/services/cache_biometria.py`; `autoponto-backend/autoponto/autoponto/settings.py` | Cache de embeddings ativos em Redis, com fallback `locmem://` para testes, compactacao dos vetores e indice `face:embeddings`. |
| Registro de presencas | `autoponto-backend/autoponto/api/models/presencas.py`; `autoponto-backend/autoponto/api/views/presencas.py`; `autoponto-backend/autoponto/api/services/sincronizacao_borda.py`; `autoponto-backend/autoponto/api/services/relatorios.py` | `RegistroPresenca`, `EventoReconhecimento`, validacao de matricula, aula, sala, dispositivo e janela temporal. |
| Relatorios | `autoponto-backend/autoponto/api/services/relatorios.py`; `autoponto-backend/autoponto/api/views/frontend.py`; `autoponto-frontend/src/features/aulas/`; `autoponto-frontend/src/features/perfil/pages/ProfilePage.tsx` | Relatorio por turma/data, resumo por turma, historico do aluno, dashboard do aluno e dashboard do professor. |
| Sincronizacao com EdgeNode | `autoponto-backend/autoponto/api/views/edge_contract.py`; `autoponto-backend/autoponto/api/services/sincronizacao_borda.py`; `autoponto-backend/autoponto/api/authentication.py`; `autoponto-backend/autoponto/api/permissions.py` | Pull de snapshot para o no, envio de presencas do EdgeNode para o servidor e autenticacao por token de no. |
| Integracao InterSCity | `autoponto-backend/autoponto/api/services/interscity.py`; `autoponto-backend/autoponto/api/views/interscity.py`; `autoponto-backend/autoponto/api/views/mapa_publico.py`; `autoponto-frontend/src/features/mapa/pages/PublicMapPage.tsx` | Diagnostico do Collector, consulta de historico, ultimos recursos, mapa publico e telemetria tecnica. |
| Telas do frontend | `autoponto-frontend/src/app/App.tsx`; `autoponto-frontend/src/app/navigation.ts`; `autoponto-frontend/src/shell/`; `autoponto-frontend/src/features/`; `autoponto-frontend/src/shared/ui/` | Rotas publicas/autenticadas, layout, navegacao por papel, dashboards, calendario, biometria, mapa e administracao. |

## 2. Metricas Simples Para Registrar Em Logs

As metricas abaixo podem ser registradas com `logger.info(...)` em JSON ou pares
`chave=valor`. Evite incluir imagem, embedding, token, senha, chave, matricula
real ou nome completo. Use IDs tecnicos ou contadores quando necessario.

| Nome da metrica | Unidade | Onde coletar no backend | Como sera usada no TCC |
|---|---:|---|---|
| `biometria_cadastro_total_ms` | ms | Ao redor de `matricular_biometria_aluno()` em `api/services/biometria.py` ou na view `MinhaBiometriaView.post()` em `api/views/frontend.py` | Medir o tempo total do fluxo de cadastro biometrico percebido pelo servidor. |
| `biometria_embedding_ms` | ms | Ao redor de `GeradorEmbeddingVisao.gerar_embedding()` e `_gerar_vetor_embedding()` em `api/services/biometria.py` | Separar custo de visao computacional do restante da persistencia. |
| `biometria_capturas_total` | contagem | Inicio de `validar_capturas_biometricas()` em `api/services/biometria.py` | Caracterizar o volume de entradas usado nos testes. |
| `biometria_capturas_decodificadas_total` | contagem | Retorno de `GeradorEmbeddingVisao.gerar_embedding()` em `api/services/biometria.py` | Indicar quantas imagens chegaram legiveis ao pipeline. |
| `biometria_faces_detectadas_total` | contagem | Campo `quantidade_faces` retornado por `GeradorEmbeddingVisao.gerar_embedding()` | Medir robustez da deteccao nas capturas de cadastro. |
| `biometria_falha_deteccao_total` | contagem | Bloco em que `gerar_embedding()` levanta `DomainValidationError` por ausencia de vetores | Quantificar falhas de deteccao facial no cadastro. |
| `embedding_criptografia_ms` | ms | Ao redor de `criptografar_vetor()` em `api/services/crypto_biometria.py` | Mostrar impacto da protecao do embedding antes de gravar. |
| `embedding_descriptografia_ms` | ms | Ao redor de `descriptografar_vetor()` em `api/services/crypto_biometria.py` e chamadas de cache/snapshot | Mostrar custo para carregar embeddings em cache ou snapshot Edge. |
| `embedding_cache_listar_ms` | ms | Ao redor de `listar_embeddings_ativos()` em `api/services/cache_biometria.py` | Avaliar tempo de leitura/sincronizacao do cache Redis de biometria. |
| `edge_snapshot_total_ms` | ms | Ao redor de `montar_payload_pull()` em `api/services/sincronizacao_borda.py` ou `EdgePullView.get()` | Medir tempo de geracao do snapshot servidor -> EdgeNode. |
| `edge_snapshot_dispositivos_total` | contagem | Dentro de `_cache_redis_snapshot()` em `api/services/sincronizacao_borda.py` | Contextualizar tamanho do snapshot enviado ao EdgeNode. |
| `edge_snapshot_aulas_total` | contagem | Dentro de `_cache_redis_snapshot()` em `api/services/sincronizacao_borda.py` | Relacionar tempo de snapshot com numero de aulas ativas. |
| `edge_snapshot_embeddings_total` | contagem | Dentro de `_cache_redis_snapshot()` em `api/services/sincronizacao_borda.py` | Relacionar tempo de snapshot com numero de embeddings entregues. |
| `edge_attendance_total_ms` | ms | Ao redor de `receber_presencas_borda()` em `api/services/sincronizacao_borda.py` ou `EdgeAttendanceView.post()` | Medir tempo de ingestao das presencas enviadas pelo EdgeNode. |
| `edge_attendance_eventos_total` | contagem | Inicio de `receber_presencas_borda()` em `api/services/sincronizacao_borda.py` | Mostrar tamanho dos lotes de presenca processados. |
| `endpoint_me_ms` | ms | Middleware simples em torno de `/api/me/` ou view `MeView.get()` | Medir endpoint de identificacao da sessao. |
| `endpoint_dashboard_aluno_ms` | ms | `DashboardAlunoView.get()` em `api/views/frontend.py` | Avaliar custo do dashboard discente. |
| `endpoint_dashboard_professor_ms` | ms | `DashboardProfessorView.get()` em `api/views/frontend.py` | Avaliar custo do dashboard docente. |
| `endpoint_calendario_ms` | ms | `MeuCalendarioAulasView.get()` em `api/views/frontend.py` | Avaliar consulta de calendario por papel. |
| `endpoint_relatorio_turma_ms` | ms | `RelatorioPresencasTurmaDataView.get()` e `RelatorioResumoTurmaView.get()` | Medir tempo de relatorios usados na analise. |
| `endpoint_mapa_nos_ms` | ms | `MapaNosPublicosView.get()` em `api/views/mapa_publico.py` | Medir resposta inicial do mapa publico. |
| `interscity_request_ms` | ms | Ao redor de `_request_status()` e `_request_json()` em `api/services/interscity.py` | Medir latencia de chamadas ao Collector. |
| `interscity_falha_total` | contagem | Nos blocos `except` de `_request_status()` e `_request_json()` em `api/services/interscity.py` | Quantificar timeout, erro HTTP e indisponibilidade externa. |
| `interscity_status` | categoria | Retornos de `ClienteInterSCity` em `api/services/interscity.py` | Classificar falhas por `ok`, `timeout`, `erro_http` e `indisponivel`. |

## 3. Sugestao De Formato De Log

Exemplo sem dados sensiveis:

```text
metric=edge_snapshot_total_ms value=42.7 node_id=<uuid> dispositivos=3 aulas=2 embeddings=18 status=ok
metric=interscity_request_ms value=311.4 service=collector operation=resources_data status=timeout
metric=biometria_embedding_ms value=890.2 capturas=3 faces=3 embeddings=3 status=ok
```

Para o TCC, os logs podem ser exportados para CSV com colunas como
`timestamp`, `metric`, `value`, `unit`, `status`, `operation`, `count`.

## 4. Capturas Recomendadas Para O TCC

As capturas devem usar dados sinteticos ou ambiente de demonstracao, nunca dados
reais de alunos. Recomenda-se gerar pares desktop/mobile em resolucoes pequenas:

| Tela | Rota | Resolucao desktop sugerida | Resolucao mobile sugerida | Secao do TCC |
|---|---|---:|---:|---|
| Login | `/signin` | 1024x720 | 390x844 | Desenvolvimento do prototipo |
| Cadastro biometrico | `/app/aluno/biometria` | 1024x720 | 390x844 | Metodologia e prototipo |
| Dashboard do professor | `/app/professor` | 1024x720 | 390x844 | Prototipo e analise |
| Calendario de aulas | `/app/calendario` | 1024x720 | 390x844 | Prototipo |
| Detalhe de aula/chamada | `/app/turmas/<turma_id>/aulas/<aula_id>` | 1024x720 | 390x844 | Fluxo de presenca |
| Frequencia do aluno | `/app/perfil` | 1024x720 | 390x844 | Analise dos resultados |
| Relatorio de presenca | tela de detalhe/frequencia da turma | 1024x720 | 390x844 | Analise dos resultados |
| Mapa IoT publico | `/mapa-iot` | 1024x720 | 390x844 | Integracao InterSCity |
| Administracao academica | `/app/admin/academico` | 1024x720 | 390x844 | Modelagem academica |
| Administracao IoT | `/app/admin/iot` | 1024x720 | 390x844 | Nos, dispositivos e InterSCity |

## 5. Observacoes De Evidencia

- O status de aula e derivado em `api/selectors/aulas.py`, nao mantido por cron.
- A sincronizacao Edge atual neste checkout esta em
  `api/services/sincronizacao_borda.py`; nao ha `api/serializers/edge.py`.
- O mapa publico usa coordenadas do `NoBorda` e dispositivos aninhados.
- O fluxo biometrico grava o vetor criptografado e descarta as capturas brutas.
- As capturas para o TCC devem ocultar nomes reais, matriculas reais e tokens.
