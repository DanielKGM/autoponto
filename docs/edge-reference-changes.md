# Ajustes Necessarios No referencia-edge

Este arquivo lista as mudancas esperadas no `referencia-edge`. O codigo de referencia nao deve ser editado neste repositorio.

## Contrato Do Servidor Principal

- Configure `MAIN_API_URL` apontando para a API principal com o prefixo `/api`, por exemplo `http://backend:8000/api`.
- Configure `MAIN_API_TOKEN` com um token emitido em `POST /api/nos-borda/{id}/emitir-token/`.
- O edge deve enviar `Authorization: NodeToken <token>`.
- O `node_id` usado no pull, push e ack deve ser o `codigo` ou UUID de `NoBorda`.
- As ESP32 nao autenticam diretamente no backend principal; elas continuam subordinadas ao Raspberry.

## Topologia

- O Raspberry e modelado como `NoBorda`.
- Cada ESP32 de sala e modelada como `DispositivoEsp32`, vinculada a um `NoBorda` e a uma `Sala`.
- O `device_id` enviado pelo edge nos eventos deve ser o UUID de `DispositivoEsp32`.
- O `locale_id` recebido no pull corresponde ao UUID de `Sala`.
- A aula concreta enviada ao edge e `Aula`, gerada a partir de `HorarioAula` dentro da janela de sincronizacao.

## Pull

`GET /api/edge/pull` e `/api/edge/pull/` seguem o formato esperado pelo edge:

```json
{
  "data": {
    "locales": [],
    "devices": [],
    "lessons": [],
    "students": [],
    "enrollments": [],
    "face_embeddings": []
  },
  "deleted": {
    "locales": [],
    "devices": [],
    "lessons": [],
    "students": [],
    "enrollments": [],
    "face_embeddings": []
  },
  "cursors": {
    "lessons": "2026-04-20T10:00:00Z"
  }
}
```

- `lessons` sao `Aula` materializadas para a janela configurada por `EDGE_SYNC_DAYS_BACK` e `EDGE_SYNC_DAYS_FORWARD`.
- `students[].registration` vem de `Usuario.matricula`.
- `face_embeddings[].embedding` vem de `EmbeddingFacial.vetor` e permanece compativel com SFace/YuNet.
- Registros inativos sao enviados em `deleted`; nao existe mais `SyncTombstone`.
- Cursores continuam sendo enviados pelo edge como `msgpack` em hexadecimal; se ausentes, a API retorna a janela completa.

## Attendance

`POST /api/edge/attendance` e `/api/edge/attendance/` recebem eventos pendentes:

```json
{
  "node_id": "NO-CCET-01",
  "events": [
    {
      "id": "edge-event-1",
      "student_id": "uuid-do-aluno",
      "lesson_id": "uuid-da-aula",
      "device_id": "uuid-da-esp32",
      "recognized_at": "2026-04-20T11:05:00Z",
      "score": 0.91
    }
  ]
}
```

- A API valida se o dispositivo pertence ao no autenticado.
- A API valida se a aula pertence a sala do dispositivo.
- A API valida se o aluno esta matriculado na turma da aula.
- Evento repetido com o mesmo `id` e idempotente: nao cria nova presenca nem novo evento.
- A resposta confirma os eventos aceitos em `synced_ids`.

## Comandos

O edge deve adicionar uma etapa no loop de sync:

- `GET /api/edge/commands?node_id=<NO_ID>` busca comandos pendentes.
- O Raspberry repassa o comando para a ESP32 correta por MQTT/local.
- `POST /api/edge/commands/ack` confirma com `DELIVERED`, `FAILED` ou `REJECTED`.

Payload de busca:

```json
{
  "commands": [
    {
      "id": "uuid-do-comando",
      "device_id": "uuid-da-esp32",
      "type": "display_message",
      "payload": {"message": "Chamada aberta"},
      "capability": "autoponto_edge_command"
    }
  ]
}
```

Payload de confirmacao:

```json
{
  "node_id": "NO-CCET-01",
  "commands": [
    {"id": "uuid-do-comando", "status": "DELIVERED"}
  ]
}
```
