# Ajustes Necessarios No referencia-edge

Este arquivo descreve o contrato que a API principal oferece ao `referencia-edge/autoponto-edgenode`. O codigo de referencia continua somente como referencia local e nao deve ser editado neste repositorio.

## Contrato Geral

- `MAIN_API_URL` deve apontar para a API principal com prefixo `/api`, por exemplo `http://backend:8000/api`.
- `MAIN_API_TOKEN` deve ser o token emitido por `POST /api/nos-borda/{id}/emitir-token/`.
- O edge envia `Authorization: NodeToken <token>` e `X-Node-Id: <node_id>`.
- `node_id` deve ser `NoBorda.codigo` ou o UUID interno do no.
- A ESP32 nao autentica no backend; ela continua subordinada ao Raspberry.

## Pull

Endpoint ativo:

```http
GET /api/edge/pull?node_id=<node_id>&cursors=<msgpack-hex>
```

Com `cursors=80`, o edge envia um dicionario msgpack vazio e recebe o cache completo do no.

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

Campos enviados:

| Modelo edge | Payload | Origem backend |
| --- | --- | --- |
| `Sala` | `salas[]` com `id`, `nome` | `Sala` |
| `Dispositivo` | `dispositivos[]` com `id`, `sala_id`, `ativo`, `interscity_uuid` | `DispositivoEsp32` |
| `Aula` | `aulas[]` com `id`, `nome`, `sala_id`, `inicio`, `fim`, `status` | `Aula` |
| `Aluno` | `alunos[]` com `id`, `matricula`, `nome` | `Usuario` aluno |
| `MatriculaAula` | `matriculas_aula[]` com `aula_id`, `aluno_id` | `MatriculaTurma` expandida por aula |
| `EmbeddingFacial` | `embeddings_faciais[]` com `id`, `aluno_id`, `vetor` | `EmbeddingFacial` ativo |

Detalhes importantes:

- `dispositivos[].id` e `deleted.dispositivos[]` usam `DispositivoEsp32.codigo`, o mesmo identificador usado pelo firmware.
- `NoBorda` nao possui recurso IntersCity. Apenas `DispositivoEsp32.interscity_uuid` representa recurso IoT.
- `alunos[]` nao envia `ativo`; aluno inativo simplesmente deixa de aparecer no cache.
- A chamada valida sempre `Aula.inicio <= reconhecido_em <= Aula.fim`.
- Aulas `FECHADA` ou `CANCELADA` aparecem em `deleted.aulas`.

## Attendance

Endpoint ativo:

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
      "reconhecido_em": "2026-04-20T08:05:00-03:00",
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

A API valida posse do dispositivo pelo no autenticado, sala da aula, matricula do aluno, intervalo da aula e status da aula. Reenvio com o mesmo `id` e idempotente.

## Status E Logs Das ESP32

`POST /api/edge/devices/status/` nao faz mais parte do contrato ativo e deve retornar 404.

O edge-node novo deve publicar status/logs diretamente no IntersCity:

1. A ESP32 recebe no MQTT local um comando JSON como `{ "stats": true }`.
2. O firmware publica em `log/{device_id}` os dados de `publishSystemStats()`.
3. O edge-node associa `device_id` ao `interscity_uuid` recebido no pull.
4. O edge-node publica no Resource Adaptor.

Capacidades esperadas no IntersCity:

- `status`
- `rssi`
- `heap_min`
- `lesson`
- `remainingms`
- `nextms`
- `now_ms`

O topico local `cmd/{device_id}` continua permitido no Raspberry para feedback imediato e para pedir stats. Ele nao representa comando vindo da API principal.
