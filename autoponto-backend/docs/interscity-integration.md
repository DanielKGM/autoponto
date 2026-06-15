# Integracao AutoPonto E Interscity

O AutoPonto continua sendo a fonte canonica para usuarios, turmas, aulas, biometria e presencas. O Interscity e usado como camada IoT observavel: catalogo, descoberta, publicacao e consulta de telemetria operacional.

## Servicos Usados

- Resource Catalog: registra recursos e capacidades.
- Resource Discovery: permite descobrir recursos por capacidades.
- Resource Adaptor: recebe dados publicados pelos recursos.
- Data Collector: guarda historico e ultimo valor das capacidades.
- Actuator Controller: fica apenas no diagnostico de disponibilidade; o MVP nao usa comandos externos.

## Recursos

- `DispositivoEsp32`: recurso IoT principal, vinculado por `DispositivoEsp32.interscity_uuid`.
- `NoBorda`: recurso opcional de infraestrutura, vinculado por `NoBorda.interscity_uuid`.
- `Sala`: continua canonica no AutoPonto; no Interscity ela aparece como metadado do recurso ESP32.

## Capacidades

- `autoponto_device_status`: sensor com `offline`, `working` ou `idle`.
- `autoponto_class_context`: informacao operacional sobre aula atual/proxima, sem dados pessoais.
- `autoponto_attendance_event`: evento anonimo/agregavel de presenca.

Comandos externos foram retirados do escopo da API principal; feedback visual/sonoro da ESP32 permanece local ao edge.

## Sincronizacao De Recursos

Endpoint administrativo:

```http
POST /api/interscity/sincronizar-recursos/
```

Para cada `DispositivoEsp32` ativo, o backend envia ao Catalog um payload semelhante a:

```json
{
  "data": {
    "uri": "autoponto://dispositivos-esp32/uuid-da-esp32",
    "description": "AutoPonto ESP32 ESP32-LAB101 - Laboratorio 101",
    "status": "active",
    "capabilities": [
      "autoponto_device_status",
      "autoponto_class_context",
      "autoponto_attendance_event"
    ],
    "metadata": {
      "autoponto_id": "uuid-da-esp32",
      "codigo": "ESP32-LAB101",
      "sala": "Laboratorio 101",
      "predio": "Centro de Ciencias Exatas e Tecnologia",
      "no": "NO-CCET-01"
    }
  }
}
```

Se o Catalog retornar um UUID, ele e salvo em `DispositivoEsp32.interscity_uuid`.

## Publicacao De Status

Fluxo:

1. ESP32 publica `sts/{device_id}` no MQTT do Raspberry.
2. Edge salva o status no Redis local.
3. Edge envia lote para `POST /api/edge/devices/status/`.
4. Backend atualiza o banco local.
5. Backend publica no Resource Adaptor quando `INTERSCITY_ENABLED=True` e existe `interscity_uuid`.

Payload publicado:

```json
{
  "data": {
    "autoponto_device_status": [
      {
        "status": "working",
        "device_id": "uuid-da-esp32",
        "node_id": "NO-CCET-01",
        "timestamp": "2026-06-15T10:30:00Z",
        "source": "edge_mqtt"
      }
    ]
  }
}
```

## Dashboard E Fallback

O painel administrativo consulta:

```http
GET /api/dispositivos-esp32/status-dashboard/?incluir_interscity=true
```

Resposta resumida:

```json
[
  {
    "id": "uuid-da-esp32",
    "codigo": "ESP32-LAB101",
    "status": "working",
    "status_efetivo": "working",
    "status_atualizado_em": "2026-06-15T10:30:00Z",
    "sala": "Laboratorio 101",
    "no": "NO-CCET-01",
    "interscity_uuid": "uuid-interscity",
    "origem_status": "local"
  }
]
```

Se o Collector responder, o campo `origem_status` pode indicar `collector`. Se Collector, Adaptor, Catalog, Discovery ou Actuator falharem, o backend retorna o snapshot local e nao bloqueia login, CRUD, biometria, presenca, relatorios ou sync edge.

## Configuracao

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

O backend monta cada URL como `INTERSCITY_BASE_URL + INTERSCITY_*_PATH`. A integracao fica desativada por padrao.

## Diagnostico

```http
GET /api/interscity/diagnostico/
```

Resposta exemplo:

```json
{
  "catalog": { "ok": true, "status": "ok" },
  "discovery": { "ok": false, "status": "timeout" },
  "collector": { "ok": false, "status": "erro_http", "codigo_http": 500 },
  "adaptor": { "ok": false, "status": "indisponivel" },
  "actuator": { "ok": false, "status": "nao_configurado" }
}
```

## Privacidade

Nao enviar ao Interscity:

- frames ou imagens;
- embeddings;
- nome de aluno;
- matricula de aluno;
- dados biometricos brutos.

Eventos de presenca publicados no futuro devem ser anonimos ou agregaveis.
