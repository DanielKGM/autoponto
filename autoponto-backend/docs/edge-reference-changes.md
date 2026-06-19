# Contrato Edge-Node AutoPonto

Este documento substitui as anotações antigas do edge. Ele descreve apenas o contrato atual que o `referencia-edge/autoponto-edgenode` deve consumir. Os arquivos de referência continuam somente para consulta e não devem ser alterados neste repositório.

## Autenticação

O Raspberry/nó de borda autentica todas as chamadas com:

```http
Authorization: NodeToken <token>
X-Node-Id: <codigo-ou-uuid-do-no>
```

- O token é emitido no backend em `POST /api/nos-borda/{id}/emitir-token/`.
- `X-Node-Id` e `node_id` devem identificar o mesmo `NoBorda`.
- A ESP32 não autentica diretamente na API principal. Ela continua subordinada ao nó de borda.

## Pull

Endpoint:

```http
GET /api/edge/pull?node_id=<node_id>&cursors=<msgpack-hex>
```

Com `cursors=80`, o edge envia um dicionário msgpack vazio e recebe o cache completo do nó.

Resposta:

```json
{
  "data": {
    "salas": [],
    "dispositivos": [],
    "aulas": [],
    "alunos": [],
    "matriculas_aula": [],
    "embeddings_faciais": []
  },
  "deleted": {
    "salas": [],
    "dispositivos": [],
    "aulas": [],
    "alunos": [],
    "matriculas_aula": [],
    "embeddings_faciais": []
  },
  "cursors": {
    "salas": "2026-06-19T12:00:00Z",
    "dispositivos": "2026-06-19T12:00:00Z",
    "aulas": "2026-06-19T12:00:00Z",
    "alunos": "2026-06-19T12:00:00Z",
    "matriculas_aula": "2026-06-19T12:00:00Z",
    "embeddings_faciais": "2026-06-19T12:00:00Z"
  }
}
```

Campos principais:

| Chave | Origem | Observação |
| --- | --- | --- |
| `salas[]` | `Sala` | Salas vinculadas às ESP32 do nó. |
| `dispositivos[]` | `DispositivoEsp32` | `id` é `DispositivoEsp32.codigo`, o mesmo identificador usado pelo firmware. |
| `aulas[]` | `Aula` | Aulas já materializadas no backend para a data atual. |
| `alunos[]` | `Usuario` aluno | Apenas alunos ativos matriculados nas aulas enviadas. |
| `matriculas_aula[]` | `MatriculaTurma` expandida por aula | Relação direta `aula_id` + `aluno_id` para o cache local. |
| `embeddings_faciais[]` | `EmbeddingFacial` ativo | Vetores necessários ao reconhecimento local do edge. |

Exemplo de aula:

```json
{
  "id": "uuid-da-aula",
  "nome": "SISTEMAS DISTRIBUIDOS - 20261EECP0021",
  "sala_id": "uuid-da-sala",
  "inicio": "2026-06-19T18:30:00-03:00",
  "fim": "2026-06-19T20:10:00-03:00",
  "status": "PLANEJADA"
}
```

Regras importantes:

- O edge recebe somente aulas já materializadas em `Aula`.
- O contrato contém somente aulas reais já materializadas.
- O pull não cria aula dinamicamente.
- O pull retorna apenas aulas da data local atual da API.
- A janela válida da presença é sempre `Aula.inicio` até `Aula.fim`.
- Aulas `FECHADA` ou `CANCELADA` aparecem em `deleted.aulas` para limpeza/indisponibilização no cache local.
- `NoBorda` não possui recurso IntersCity; apenas `DispositivoEsp32.interscity_uuid` representa recurso IoT.

## Attendance

Endpoint:

```http
POST /api/edge/attendance
```

Payload:

```json
{
  "node_id": "NO-CCET-01",
  "eventos": [
    {
      "id": "edge-event-1",
      "aluno_id": "uuid-do-aluno",
      "aula_id": "uuid-da-aula",
      "dispositivo_id": "ESP32-LAB101",
      "reconhecido_em": "2026-06-19T18:45:00-03:00",
      "score": 0.91
    }
  ]
}
```

Resposta:

```json
{
  "synced_ids": ["edge-event-1"]
}
```

Validações feitas pela API:

- O token pertence ao nó informado.
- `dispositivo_id` existe como `DispositivoEsp32.codigo`, está ativo e pertence ao nó autenticado.
- A aula existe e está na mesma sala da ESP32.
- O aluno existe, está ativo e está matriculado na turma da aula.
- `reconhecido_em` está entre `Aula.inicio` e `Aula.fim`.
- A aula não está `FECHADA` nem `CANCELADA`.
- Reenvio com o mesmo `id` é idempotente.

## IntersCity

O backend não recebe status/logs das ESP32 pelo contrato edge. O uso atual do IntersCity fica no edge-node:

1. O edge-node pede estatísticas à ESP32 pelo MQTT local, usando `cmd/{device_id}` com `{ "stats": true }`.
2. A ESP32 publica o resultado em `log/{device_id}`.
3. O edge-node associa `device_id` ao `interscity_uuid` recebido no pull.
4. O edge-node publica a telemetria no Resource Adaptor do IntersCity.

Capacidades esperadas:

- `status`
- `rssi`
- `heap_min`
- `lesson`
- `remainingms`
- `nextms`
- `now_ms`

Não há endpoint ativo de comandos externos do backend para o edge. O tópico MQTT local `cmd/{device_id}` continua sendo responsabilidade do nó de borda.
