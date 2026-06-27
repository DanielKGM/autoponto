# Integracao AutoPonto E IntersCity

## Papel Atual No MVP

O AutoPonto continua canonico para usuarios, turmas, aulas, biometria, presencas e relatorios. O IntersCity fica restrito a observabilidade IoT das ESP32.

Nao existem recursos IntersCity para `NoBorda`. Cada recurso IntersCity representa uma ESP32 cadastrada em `DispositivoEsp32.interscity_uuid`.

## Fluxo Operacional

1. A API principal envia ao edge, em `GET /api/edge/pull`, cada ESP32 com `codigo`, `sala_id` e `interscity_uuid`.
2. O edge-node usa esse UUID para publicar diretamente no Resource Adaptor.
3. O Data Collector armazena historico das capacidades tecnicas.
4. A API principal oferece endpoints publicos de mapa para listar ESP32 cadastradas e consultar historico do Collector sob demanda.

```mermaid
sequenceDiagram
    participant ESP as ESP32
    participant Edge as Edge-node
    participant API as API AutoPonto
    participant IC as IntersCity
    participant Front as Mapa publico

    Edge->>API: GET /api/edge/pull
    API-->>Edge: dispositivos com interscity_uuid
    ESP-->>Edge: log/{device_id}
    Edge->>IC: POST /adaptor/resources/{uuid}/data
    Front->>API: GET /api/public/mapa/dispositivos/
    API-->>Front: ESP32 + latitude/longitude + uuid
    Front->>API: GET /api/public/mapa/dispositivos/{id}/historico/?dias=7
    API->>IC: POST /collector/resources/data
    API-->>Front: historico filtrado + ultimo valor
```

## Capacidades Do Mapa

O proxy publico da API filtra apenas capacidades operacionais:

- `status`
- `rssi`
- `heap_min`
- `lesson`
- `remainingms`
- `nextms`
- `now_ms`

Dados biometricos, imagens, embeddings, nomes de alunos e presencas individuais nao entram no IntersCity.

## Publicacao Pelo Edge

Payload esperado ao Resource Adaptor:

```json
{
  "data": {
    "status": [
      {
        "value": "idle"
      }
    ],
    "rssi": [
      {
        "value": -61
      }
    ],
    "heap_min": [
      {
        "value": 120000
      }
    ],
    "lesson": [
      {
        "value": "Desenvolvimento de Sistemas Web - A"
      }
    ],
    "remainingms": [
      {
        "value": 500000
      }
    ],
    "nextms": [
      {
        "value": 1200000
      }
    ],
    "now_ms": [
      {
        "value": 12345678
      }
    ]
  }
}
```

O nome exato do envelope pode variar conforme o Resource Adaptor usado, mas o Data Collector deve expor essas capacidades em `/collector/resources/data`.

## Endpoints Da API Principal

- `GET /api/interscity/diagnostico/`: diagnostico administrativo dos microsservicos.
- `GET /api/public/mapa/dispositivos/`: lista ESP32 ativas com `interscity_uuid`, latitude e longitude.
- `GET /api/public/mapa/dispositivos/{id}/historico/?dias=7`: consulta o Data Collector via proxy tolerante a falhas.

O endpoint de historico chama:

```http
POST {INTERSCITY_BASE_URL}{INTERSCITY_COLLECTOR_PATH}/resources/data
```

Com corpo:

```json
{
  "uuids": ["uuid-da-esp32"],
  "capabilities": [
    "status",
    "rssi",
    "heap_min",
    "lesson",
    "remainingms",
    "nextms",
    "now_ms"
  ],
  "start_date": "2026-06-12T12:00:00Z",
  "end_date": "2026-06-19T12:00:00Z"
}
```

## Variaveis

```env
INTERSCITY_BASE_URL=https://cidadesinteligentes.lsdi.ufma.br/interscity_lh
INTERSCITY_CATALOG_PATH=/catalog
INTERSCITY_DISCOVERY_PATH=/discovery
INTERSCITY_COLLECTOR_PATH=/collector
INTERSCITY_ADAPTOR_PATH=/adaptor
INTERSCITY_ACTUATOR_PATH=/actuator
INTERSCITY_TIMEOUT_SECONDS=5
```

Falhas externas nao bloqueiam login, CRUD, biometria, presencas, relatorios ou sync edge.
