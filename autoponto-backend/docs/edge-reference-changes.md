# Ajustes Necessarios No referencia-edge

Este arquivo lista mudancas esperadas no `referencia-edge`. O codigo de referencia continua somente como referencia local e nao deve ser editado neste repositorio.

## Contrato Geral

- Configure `MAIN_API_URL` apontando para a API principal com prefixo `/api`, por exemplo `http://backend:8000/api`.
- Configure `MAIN_API_TOKEN` com token emitido por `POST /api/nos-borda/{id}/emitir-token/`.
- O edge deve enviar `Authorization: NodeToken <token>`.
- O `node_id` usado nos endpoints deve ser o `codigo` ou UUID de `NoBorda`.
- ESP32 nao autentica diretamente no backend principal; ela continua subordinada ao Raspberry.

## Pull

`GET /api/edge/pull` e `/api/edge/pull/` retornam salas, dispositivos, aulas, alunos, matriculas e embeddings:

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

Exemplo de aula:

```json
{
  "id": "uuid-da-aula",
  "name": "Desenvolvimento de Sistemas Web - A",
  "locale_id": "uuid-da-sala",
  "starts_at": "2026-04-20T08:00:00Z",
  "ends_at": "2026-04-20T09:40:00Z",
  "status": "PLANEJADA"
}
```

Mudancas importantes:

- Campos separados de validade manual foram removidos.
- O intervalo valido da chamada e sempre `starts_at <= recognized_at <= ends_at`.
- Aulas `FECHADA` ou `CANCELADA` aparecem em `deleted.lessons` para o edge remover/desabilitar no cache local.
- `devices[].status` informa o status efetivo conhecido pelo backend: `offline`, `working` ou `idle`.
- Cursores continuam sendo enviados pelo edge como `msgpack` em hexadecimal.

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
      "recognized_at": "2026-04-20T08:05:00Z",
      "score": 0.91
    }
  ]
}
```

A API valida:

- dispositivo pertence ao no autenticado;
- aula pertence a sala do dispositivo;
- aluno esta matriculado na turma da aula;
- `recognized_at` esta entre `Aula.inicio` e `Aula.fim`;
- aula nao esta `FECHADA` nem `CANCELADA`.

Evento repetido com o mesmo `id` e idempotente. A resposta confirma os eventos aceitos:

```json
{"synced_ids": ["edge-event-1"]}
```

## Status Das ESP32

O firmware publica status no MQTT local do Raspberry:

```text
sts/{device_id}
```

Payload esperado:

```text
offline
working
idle
```

O `referencia-edge` ja possui a base desse fluxo em:

```python
client.subscribe("sts/+")
save_device_status(device_id, state)
```

e salva no Redis:

```text
device:{device_id}:status
devices:last_seen
```

Mudanca sugerida no loop de sync do edge: ler esses status do Redis e enviar periodicamente ao backend:

```http
POST /api/edge/devices/status/
```

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

O backend atualiza `DispositivoEsp32.status`, `status_atualizado_em` e publica `autoponto_device_status` no Interscity quando configurado.

## Comandos

Nao existem mais comandos vindos da API principal para o edge neste MVP.

O topico MQTT local `cmd/{device_id}`, usado pelo `referencia-edge` para feedback imediato da ESP32 apos reconhecimento, pode continuar existindo no Raspberry. Ele nao e fila de comando do backend e nao tem endpoints correspondentes na API principal.
