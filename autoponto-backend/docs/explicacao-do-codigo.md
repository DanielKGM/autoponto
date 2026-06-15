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

Codigo composto como `25M34` vira duas linhas: `2M34` e `5M34`. Assim uma turma pode ter mais de um `HorarioAula`, cada um apontando para um horario padrao.

### HorarioAula

- `turma`: turma daquele horario.
- `sala`: sala onde a aula acontece.
- `horario_padrao`: bloco UFMA tabelado.
- `ativo`: desativa o vinculo sem apagar aulas ja criadas.

Se o horario padrao mudar, novas aulas usam o novo horario. Aulas ja criadas preservam `inicio` e `fim`.

### Aula

- `horario`: regra semanal que gerou a aula.
- `data`: data da aula.
- `inicio` e `fim`: snapshot real da aula naquela data.
- `status`: `PLANEJADA`, `ABERTA`, `FECHADA` ou `CANCELADA`.
- `fechada_em`: quando professor/admin fechou manualmente.
- `fechada_por`: usuario que fechou.

A chamada vale sempre entre `inicio` e `fim`. Fechar manualmente nao altera `fim`; apenas impede novas presencas.

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
- `NoBorda.interscity_uuid`: recurso equivalente no Interscity, se existir.
- `TokenNoBorda.no`: dono do token.
- `TokenNoBorda.prefixo_token`: trecho visivel do segredo.
- `TokenNoBorda.hash_token`: hash do token real.
- `TokenNoBorda.ativo`, `expira_em`, `ultimo_uso_em`: seguranca e rotacao.
- `DispositivoEsp32.no`: Raspberry responsavel.
- `DispositivoEsp32.sala`: sala monitorada.
- `DispositivoEsp32.codigo`: identificador da ESP32.
- `DispositivoEsp32.nome`: nome administrativo.
- `DispositivoEsp32.ativo`: controla envio ao edge.
- `DispositivoEsp32.status`: `offline`, `working` ou `idle`.
- `DispositivoEsp32.status_atualizado_em`: instante informado pelo edge.
- `DispositivoEsp32.status_efetivo`: propriedade calculada; vira `offline` se o status estiver velho.
- `DispositivoEsp32.interscity_uuid`: recurso IoT no Interscity.

### PerfilBiometrico E EmbeddingFacial

- `PerfilBiometrico.aluno`: dono da biometria.
- `PerfilBiometrico.status`: `PENDENTE`, `ATIVO` ou `INATIVO`.
- `EmbeddingFacial.perfil`: perfil dono do vetor.
- `EmbeddingFacial.versao_modelo`: modelo usado, como `sface`.
- `EmbeddingFacial.vetor`: embedding facial enviado ao edge.
- `EmbeddingFacial.status`: `ATIVO`, `INATIVO` ou `REVOGADO`.
- `EmbeddingFacial.ativo`: garante apenas um embedding ativo por aluno.

O backend compara o novo vetor com embeddings ativos de outros alunos e bloqueia duplicidade por `FACE_DUPLICATE_THRESHOLD`.

## Sincronizacao Edge

O Raspberry autentica com:

```http
Authorization: NodeToken <token>
```

### Pull

`GET /api/edge/pull` chama `montar_payload_pull(no, query_params)`.

Trecho essencial:

```python
for data in _intervalo_datas(data_inicio, data_fim):
    for sala in salas_ativas:
        aulas.extend(listar_aulas_do_dia(data, sala=sala))
```

O backend materializa aulas, busca matriculas e embeddings, e retorna:

- `locales`: salas;
- `devices`: ESP32 do no;
- `lessons`: aulas com `starts_at` e `ends_at`;
- `students`: alunos matriculados;
- `enrollments`: aluno por aula;
- `face_embeddings`: vetor ativo.

### Attendance

`POST /api/edge/attendance` chama `receber_presencas_borda`.

Validacao central:

```python
if aula.status in {Aula.STATUS_FECHADA, Aula.STATUS_CANCELADA}:
    raise ValidationError(...)
if reconhecido_em < aula.inicio or reconhecido_em > aula.fim:
    raise ValidationError(...)
```

Se valido, o backend faz `update_or_create` de `RegistroPresenca` e cria `EventoReconhecimento`. Evento repetido retorna o mesmo id em `synced_ids`.

### Status De Dispositivos

`POST /api/edge/devices/status/` chama `atualizar_status_dispositivos_borda`.

Payload:

```json
{
  "node_id": "NO-CCET-01",
  "devices": [
    {
      "device_id": "uuid-da-esp32",
      "status": "working",
      "reported_at": "2026-06-15T10:30:00Z"
    }
  ]
}
```

Trecho essencial:

```python
dispositivo.status = status_normalizado
dispositivo.status_atualizado_em = reportado_em
publicar_status_dispositivo_interscity(dispositivo, reportado_em=reportado_em)
```

O status vem do MQTT local `sts/{device_id}` no edge. O backend so aceita status de dispositivos pertencentes ao no autenticado.

## Interscity

`ClienteInterSCity` monta URLs a partir de `INTERSCITY_BASE_URL` e paths dos microsservicos. Todas as chamadas usam timeout e retornam erro controlado.

Uso atual:

- registrar/atualizar ESP32 no Catalog;
- publicar `autoponto_device_status` no Adaptor;
- consultar ultimo status no Collector para enriquecer dashboard;
- diagnosticar Catalog, Discovery, Collector, Adaptor e Actuator.

Falha externa nao bloqueia o AutoPonto; o banco local e o fallback.

## Biometria

O backend usa OpenCV YuNet/SFace com os mesmos ONNX do edge:

- `data/models/face_detection_yunet.onnx`;
- `data/models/face_recognition_sface.onnx`.

As imagens/base64 sao processadas e descartadas. Apenas embedding e metadados seguros ficam persistidos.

## Testes

- `test_models.py`: regras de dominio, horario UFMA, unicidade e biometria ativa.
- `test_edge_integracao.py`: pull, attendance, idempotencia, isolamento por no e status ESP32.
- `test_frontend_api.py`: endpoints por papel, relatorios, fechamento e dashboard.
- `test_interscity.py`: cliente HTTP, diagnostico, Catalog e falhas.
- `test_seguranca.py`: isolamento por papel, NodeToken, biometria e cookie de refresh.
