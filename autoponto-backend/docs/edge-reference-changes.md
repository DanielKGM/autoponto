# Ajustes Necessarios No referencia-edge

Este arquivo lista mudancas esperadas no `referencia-edge`. O codigo de referencia continua somente como referencia local e nao deve ser editado neste repositorio.

## Contrato Geral Com A API Principal

- Configure `MAIN_API_URL` apontando para a API principal com prefixo `/api`, por exemplo `http://backend:8000/api`.
- Configure `MAIN_API_TOKEN` com token emitido por `POST /api/nos-borda/{id}/emitir-token/`.
- O edge deve enviar `Authorization: NodeToken <token>`.
- O `node_id` usado nos endpoints deve ser o `codigo` ou UUID de `NoBorda`.
- ESP32 nao autentica diretamente no backend principal; ela continua subordinada ao Raspberry.

## Coerencia De Modelos Edge/API

A API principal usa nomes internos em portugues, mas o payload de sincronizacao mantem nomes compativeis com `referencia-edge/services/edge-app/app/models.py`:

| Edge model | Payload da API | Origem no backend |
| --- | --- | --- |
| `Locale` | `locales[]` com `id`, `name` | `Sala` |
| `Device` | `devices[]` com `id`, `locale_id`, `active`, `status` | `DispositivoEsp32` |
| `Lesson` | `lessons[]` com `id`, `name`, `locale_id`, `starts_at`, `ends_at`, `status` | `Aula` |
| `Student` | `students[]` com `id`, `registration`, `name`, `active` | `Usuario` aluno |
| `Enrollment` | `enrollments[]` | `MatriculaTurma` expandida por aula |
| `FaceEmbedding` | `face_embeddings[]` | `EmbeddingFacial` ativo |
| `AttendanceEvent` | push em `/api/edge/attendance` | evento pendente do edge |

Mudanca sugerida no edge: adicionar campos opcionais `status` em `Device` e `Lesson`, mantendo compatibilidade com payload antigo.

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

O intervalo valido da chamada e sempre `starts_at <= recognized_at <= ends_at`. Aulas `FECHADA` ou `CANCELADA` aparecem em `deleted.lessons` para o edge remover/desabilitar no cache local.

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

A API valida posse do dispositivo, sala da aula, matricula do aluno, intervalo da aula e status da aula. Evento repetido com o mesmo `id` e idempotente.

## Status Local Das ESP32 Na API Principal

O firmware publica status simples no MQTT local:

```text
sts/{device_id}
```

Payload esperado:

```text
offline
working
idle
```

O edge ja assina `sts/+` em `app/mqtt.py` e salva esse snapshot. Mudanca sugerida no loop de sync: ler os status salvos no Redis e enviar para a API principal:

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

Esse endpoint atualiza somente o snapshot local da API principal. Ele nao publica no IntersCity.

## Publicacao De Stats No IntersCity Pelo Edge

O IntersCity, no escopo atual, deve ser alimentado diretamente pelo edge-node, nao pela API principal.

Mudancas sugeridas no `referencia-edge`:

1. Assinar tambem `log/+` no MQTT local, alem de `sts/+`.
2. Publicar periodicamente em `cmd/{device_id}` um comando JSON para pedir stats ao firmware:

```json
{ "stats": true }
```

3. Receber em `log/{device_id}` o payload gerado pelo firmware em `publishSystemStats()`:

```json
{
  "id": "uuid-da-esp32",
  "state": "idle",
  "cpu_freq": 240,
  "rssi": -61,
  "heap_free": 180000,
  "heap_min": 120000,
  "now_ms": 12345678,
  "context": {
    "lesson": "Desenvolvimento de Sistemas Web - A",
    "remaining_ms": 500000,
    "next_ms": 1200000
  }
}
```

4. Publicar esse dado no Resource Adaptor usando uma capability unica, por exemplo `autoponto_device_stats`.
5. Manter o UUID/recurso IntersCity por configuracao do edge-node ou por cadastro manual na plataforma.

Exemplo de payload ao Resource Adaptor:

```json
{
  "data": {
    "autoponto_device_stats": [
      {
        "device_id": "uuid-da-esp32",
        "state": "idle",
        "rssi": -61,
        "now_ms": 12345678,
        "context": {
          "lesson": "Desenvolvimento de Sistemas Web - A",
          "remaining_ms": 500000,
          "next_ms": 1200000
        },
        "source": "edge_mqtt_log"
      }
    ]
  }
}
```

## Comandos

Nao existem comandos vindos da API principal para o edge neste MVP.

O topico MQTT local `cmd/{device_id}` continua permitido dentro do Raspberry para feedback imediato da ESP32 e para solicitar `stats=true`. Ele nao representa fila de comandos do backend e nao possui endpoints correspondentes na API principal.
