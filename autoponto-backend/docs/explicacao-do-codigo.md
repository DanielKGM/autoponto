# Explicacao Geral Do Backend

O backend e uma API Django/DRF para frequencia academica automatizada por IoT. Ele guarda apenas o necessario para presenca, biometria, relatorios, sincronizacao com Raspberry/ESP32 e integracao Interscity.

## Organizacao

- `api/models/`: tabelas e integridade de negocio.
- `api/serializers/`: validacao de entrada e saida JSON.
- `api/views/`: endpoints HTTP para frontend, admin, edge e Interscity.
- `api/services/`: regras reutilizaveis de aula, biometria, relatorios, sync e Interscity.
- `api/tests/`: contratos principais do MVP.
- `data/models/`: modelos ONNX YuNet/SFace usados na biometria.

Todos os modelos de dominio herdam `BaseModel`, que adiciona `id` UUID, `criado_em` e `atualizado_em`.

## Modelos E Campos

### Usuario

- `username`: login.
- `email`: contato.
- `papel`: `ALUNO`, `PROFESSOR` ou `ADMINISTRADOR`.
- `matricula`: codigo institucional do aluno.
- `nome_completo`: nome exibido em telas e relatorios.
- Campos Django como `password`, `is_active`, `is_staff` e `is_superuser`: autenticacao e admin.

### Campus, Predio E Sala

- `Campus.nome`: campus usado no projeto.
- `Campus.ativo`: permite ocultar sem apagar historico.
- `Predio.campus`: campus onde o predio fica.
- `Predio.nome`: centro, bloco ou predio.
- `Predio.ativo`: controla uso em cadastros.
- `Sala.predio`: predio da sala.
- `Sala.nome`: nome legivel.
- `Sala.codigo`: identificador curto util para salas/laboratorios.
- `Sala.ativo`: se falso, deixa de ir para o edge.

### PeriodoLetivo, Curso, Disciplina E Turma

- `PeriodoLetivo.nome`: exemplo `2026.1`.
- `PeriodoLetivo.data_inicio` e `data_fim`: intervalo em que turmas geram aulas.
- `PeriodoLetivo.ativo`: periodo usado nas telas de aluno.
- `Curso.campus`: campus do curso.
- `Curso.nome`: exemplo `Engenharia da Computacao`.
- `Curso.ativo`: controla listagem/cadastro.
- `Disciplina.curso`: curso dono da disciplina.
- `Disciplina.codigo`: codigo institucional da disciplina.
- `Disciplina.nome`: nome exibido em relatorios.
- `Disciplina.ativo`: controla uso na sincronizacao.
- `Turma.periodo_letivo`: semestre da turma.
- `Turma.disciplina`: disciplina ministrada.
- `Turma.codigo`: identificador da turma, como `A` ou `01`.
- `Turma.professores`: professores autorizados a relatorios e fechamento manual.
- `Turma.ativo`: se falso, deixa de gerar contexto para edge.

### MatriculaTurma

- `turma`: turma do aluno.
- `aluno`: usuario com papel `ALUNO`.
- `ativo`: se falso, aluno deixa de aparecer na sincronizacao.

Ausencia nao e linha persistida. Relatorios calculam ausencia quando nao existe `RegistroPresenca`.

### HorarioPadraoUFMA

Tabela os horarios no formato usado pela UFMA/SIGAA.

- `codigo`: codigo normalizado por dia, como `2M12` ou `5M34`.
- `dia_semana`: choices UFMA `2` a `7`, de segunda a sabado.
- `horario_inicio`: inicio real do bloco.
- `horario_fim`: fim real do bloco.
- `ativo`: permite desativar blocos antigos.

Codigo composto como `25M34` vira duas linhas: `2M34` e `5M34`. Ao criar ou editar uma turma, o administrador informa uma lista de pares `sala` + `horario_padrao`; o backend materializa as aulas reais desse periodo letivo.

### Aula

- `turma`: turma daquela ocorrencia.
- `sala`: sala onde a aula acontece.
- `horario_padrao`: bloco UFMA usado como referencia na criacao.
- `data`: data da aula.
- `inicio` e `fim`: snapshot real da aula naquela data.
- `status`: `PLANEJADA`, `ABERTA`, `FECHADA` ou `CANCELADA`.
- `fechada_em`: quando professor/admin fechou manualmente.
- `fechada_por`: usuario que fechou.

A chamada vale sempre entre `inicio` e `fim`. Fechar manualmente nao altera `fim`; apenas impede novas presencas.
Aulas com presenca registrada preservam o historico mesmo se a turma for editada depois.

### RegistroPresenca

- `aula`: aula da presenca.
- `aluno`: aluno presente.
- `status`: `PRESENTE`, `AUSENTE`, `ATRASO` ou `JUSTIFICADA`.
- `registrado_em`: instante do reconhecimento ou registro manual.
- `registrado_por_dispositivo`: ESP32 que originou a presenca, quando veio do edge.

Ha no maximo uma presenca por aluno/aula.

### EventoReconhecimento

- `id_evento_origem`: id gerado no edge para idempotencia.
- `dispositivo`: ESP32 que originou o evento.
- `aula`: aula associada.
- `aluno_candidato`: aluno reconhecido.
- `confianca`: score do reconhecimento.
- `reconhecido`: indica se gerou presenca.
- `ocorrido_em`: instante do reconhecimento.

Nao salva imagem, frame, embedding bruto de captura nem payload tecnico bruto.

### NoBorda, TokenNoBorda E DispositivoEsp32

- `NoBorda.codigo`: identificador usado em `node_id`.
- `NoBorda.nome`: nome administrativo.
- `NoBorda.ativo`: controla autenticacao.
- `NoBorda.ultimo_sync_em`: ultima sincronizacao.
- `TokenNoBorda.no`: dono do token.
- `TokenNoBorda.prefixo_token`: trecho visivel do segredo.
- `TokenNoBorda.hash_token`: hash do token real.
- `TokenNoBorda.ativo`, `expira_em`, `ultimo_uso_em`: seguranca e rotacao.
- `DispositivoEsp32.no`: Raspberry responsavel.
- `DispositivoEsp32.sala`: sala monitorada.
- `DispositivoEsp32.codigo`: identificador da ESP32.
- `DispositivoEsp32.nome`: nome administrativo.
- `DispositivoEsp32.ativo`: controla envio ao edge.
- `DispositivoEsp32.interscity_uuid`: recurso IoT no Interscity.
- `DispositivoEsp32.latitude` e `longitude`: coordenadas usadas pelo mapa publico.

### EmbeddingFacial

- `EmbeddingFacial.aluno`: aluno dono do vetor biometrico.
- `EmbeddingFacial.versao_modelo`: modelo usado, como `sface`.
- `EmbeddingFacial.vetor`: embedding facial enviado ao edge.
- `EmbeddingFacial.status`: `ATIVO`, `INATIVO` ou `REVOGADO`.
- `EmbeddingFacial.ativo`: indica se o unico embedding do aluno esta disponivel para sincronizacao.

Existe apenas um `EmbeddingFacial` por aluno. Ao cadastrar um novo rosto, o backend atualiza esse registro e o vetor anterior e perdido. Antes da atualizacao, o backend compara o novo vetor com embeddings ativos de outros alunos e bloqueia duplicidade por `FACE_DUPLICATE_THRESHOLD`.

## Sincronizacao Edge

O Raspberry autentica com:

```http
Authorization: NodeToken <token>
```

### Pull

`GET /api/edge/pull` chama `montar_payload_pull(no, query_params)`.

Trecho essencial:

```python
return {
    "snapshot_data": data_do_snapshot,
    "synced_at": instante_da_sincronizacao,
    "cache_redis": mapas_prontos_para_o_edge,
}
```

O backend consulta as aulas do dia local atual da API, que ja foram materializadas quando a turma foi cadastrada/editada. O pull e sempre um snapshot autoritativo pronto para Redis: o edge grava `cache_redis` diretamente com `substituir_snapshot_redis`, entao nao existem entidades completas no payload, cursores, payload incremental nem lista `deleted`.

- `dispositivos_por_codigo`: ESP32 do no indexadas por `codigo`, com UUID da API e sala;
- `aulas_por_sala`: aulas validas do dia agrupadas por sala e ordenadas por inicio;
- `alunos_por_aula`: ids dos alunos por aula;
- `alunos_por_id`: metadados minimos dos alunos, incluindo `nome`;
- `embeddings_faciais`: ciphertext Fernet do vetor ativo; o EdgeNode descriptografa antes do face-worker.

### Attendance

`POST /api/edge/attendance` chama `receber_presencas_borda` e recebe `eventos` com campos em portugues: `aluno_id`, `aula_id`, `dispositivo_id` e `reconhecido_em`. O campo `dispositivo_id` e o UUID de `DispositivoEsp32.id`, nao o `codigo` do firmware.

Validacao central:

```python
if aula.status in {Aula.STATUS_FECHADA, Aula.STATUS_CANCELADA}:
    raise ValidationError(...)
if reconhecido_em < aula.inicio or reconhecido_em > aula.fim:
    raise ValidationError(...)
```

Se valido, o backend faz `update_or_create` de `RegistroPresenca` e cria `EventoReconhecimento`. Evento repetido retorna o mesmo id em `synced_ids`.

`POST /api/edge/devices/status/` nao existe mais. Status e logs das ESP32 sao publicados pelo edge diretamente no Interscity.

## Interscity

`ClienteInterSCity` monta URLs a partir de `INTERSCITY_BASE_URL` e paths dos microsservicos. Todas as chamadas usam timeout e retornam erro controlado.

Uso atual:

- diagnosticar Catalog, Discovery, Collector, Adaptor e Actuator;
- listar ESP32 publicas para o mapa com `GET /api/public/mapa/dispositivos/`;
- consultar historico operacional no Collector com `GET /api/public/mapa/dispositivos/{id}/historico/?dias=7`.

A publicacao de telemetria no IntersCity fica no edge-node, que envia dados da ESP32 diretamente ao Resource Adaptor. A API principal consulta somente o Data Collector quando o mapa publico solicita historico.

Falha externa nao bloqueia o AutoPonto; o banco local e o fallback.

## Biometria

O backend usa OpenCV YuNet/SFace com os mesmos ONNX do edge:

- `data/models/face_detection_yunet.onnx`;
- `data/models/face_recognition_sface.onnx`.

As imagens/base64 sao processadas e descartadas. Apenas embedding e metadados seguros ficam persistidos.

## Testes

- `test_models.py`: regras de dominio, horario UFMA, unicidade e biometria ativa.
- `test_edge_integracao.py`: pull, attendance, idempotencia, isolamento por no e remocao do status endpoint.
- `test_mapa_publico.py`: mapa publico e historico IntersCity via Collector.
- `test_frontend_api.py`: endpoints por papel, relatorios, fechamento e cadastros para dashboard.
- `test_interscity.py`: diagnostico tolerante a falhas dos microsservicos IntersCity.
- `test_seguranca.py`: isolamento por papel, NodeToken, biometria e cookie de refresh.
