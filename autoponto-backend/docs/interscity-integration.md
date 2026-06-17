# Integracao AutoPonto E IntersCity

## Papel Atual No MVP

O AutoPonto principal nao publica nem sincroniza recursos de negocio no IntersCity neste momento. A API principal continua canonica para usuarios, turmas, aulas, biometria, presencas e relatorios.

No MVP atual, o IntersCity sera usado somente como camada de observabilidade IoT alimentada pelo `edge-node`. O Raspberry solicita estatisticas das ESP32 por MQTT, recebe o payload de log do firmware e publica periodicamente esses dados diretamente no Resource Adaptor.

## Fluxo Definido

1. O firmware da ESP32 recebe pelo MQTT local um comando JSON com `stats=true`.
2. A ESP32 executa `publishSystemStats()` e publica em `log/{device_id}`.
3. O edge-node assina `log/+`, valida o payload e associa o `device_id` ao recurso IntersCity configurado.
4. O edge-node publica no Resource Adaptor.
5. O Data Collector passa a armazenar o ultimo estado operacional.
6. Futuramente, uma pagina publica do AutoPonto podera consultar Discovery/Collector sob demanda, com botao de atualizar mapa, sem websocket/webhook.

## Capability Unica Do MVP

Capability sugerida:

```text
autoponto_device_stats
```

Payload publicado pelo edge-node no IntersCity:

```json
{
  "data": {
    "autoponto_device_stats": [
      {
        "device_id": "uuid-da-esp32",
        "state": "idle",
        "rssi": -61,
        "now_ms": 12345678,
        "cpu_freq": 240,
        "heap_free": 180000,
        "heap_min": 120000,
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

Dados biometricos, imagens, embeddings, nomes de alunos e presencas individuais nao entram no IntersCity.

## Uso Da API Principal

A API principal mantem apenas:

- `GET /api/interscity/diagnostico/`: endpoint administrativo para verificar disponibilidade de Catalog, Discovery, Collector, Adaptor e Actuator.
- Campos `interscity_uuid` em modelos de infraestrutura: ficam reservados para mapeamento futuro ou cadastro manual de recursos, mas o backend nao chama Catalog/Adaptor no fluxo atual.

Nao existe mais endpoint de sincronizacao de recursos IntersCity no backend.

## Variaveis

```env
INTERSCITY_ENABLED=False
INTERSCITY_BASE_URL=https://cidadesinteligentes.lsdi.ufma.br/interscity_lh
INTERSCITY_CATALOG_PATH=/catalog
INTERSCITY_DISCOVERY_PATH=/discovery
INTERSCITY_COLLECTOR_PATH=/collector
INTERSCITY_ADAPTOR_PATH=/adaptor
INTERSCITY_ACTUATOR_PATH=/actuator
INTERSCITY_TIMEOUT_SECONDS=5
```

Mesmo com `INTERSCITY_ENABLED=True`, falhas desses microsservicos nao bloqueiam login, CRUD, biometria, presencas, relatorios ou sync edge.
