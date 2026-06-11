# Integracao AutoPonto E Interscity

O AutoPonto continua sendo a fonte canonica para dominio academico, biometria, aulas e presencas. O Interscity fica centralizado na camada IoT: catalogo de recursos, capacidades, telemetria operacional, descoberta e comandos.

## Servicos Usados

- Resource Catalog: registra recursos e capacidades.
- Resource Adaptor: recebe dados de recursos e encaminha comandos.
- Data Collector: disponibiliza historico e ultimo valor dos dados publicados.
- Resource Discovery: descobre recursos por capacidade, localizacao e filtros.
- Actuator Controller: cria comandos para recursos atuadores.

O cliente `ClienteInterSCity` possui metodos para esses cinco pontos: `registrar_recurso_catalogo`, `publicar_dados_recurso`, `consultar_dados_coletor`, `descobrir_recursos` e `enviar_comando_atuador`.

## Recursos

- ESP32/sala: recurso IoT principal, vinculado a `DispositivoEsp32.interscity_uuid`.
- Raspberry/no: recurso opcional de infraestrutura, vinculado a `NoBorda.interscity_uuid`.
- `Sala` continua sendo o local canonico no AutoPonto; no Interscity ela aparece indiretamente pelo recurso da ESP32.

## Capacidades Iniciais

- `autoponto_device_status` como `sensor`.
- `autoponto_class_context` como `information`.
- `autoponto_attendance_event` como `sensor`.
- `autoponto_edge_command` como `actuator`.

## Publicacao De Dados

A publicacao operacional usa o Resource Adaptor:

```http
POST /resources/{uuid}/data
```

Payload:

```json
{
  "data": {
    "autoponto_device_status": [
      {
        "status": "online",
        "date": "2026-04-20T10:00:00Z"
      }
    ]
  }
}
```

Eventos de presenca devem ser agregaveis e anonimizados quando publicados fora do AutoPonto:

```json
{
  "data": {
    "autoponto_attendance_event": [
      {
        "lesson_id": "uuid-da-aula",
        "device_id": "uuid-da-esp32",
        "recognized": true,
        "score_bucket": "0.90-0.95",
        "date": "2026-04-20T11:05:00Z"
      }
    ]
  }
}
```

Por padrao, nao enviar ao Interscity:

- frames ou imagens;
- embeddings;
- nome de aluno;
- matricula de aluno;
- dados biometricos brutos.

## Comandos

O Resource Adaptor chama a API principal em:

```http
POST /api/interscity/webhooks/actuator/
```

Payload esperado:

```json
{
  "action": "actuator_command",
  "command": {
    "_id": {"$oid": "59395c1329d4b10379bed679"},
    "uuid": "uuid-do-recurso-interscity",
    "capability": "autoponto_edge_command",
    "value": {
      "type": "display_message",
      "payload": {"message": "Chamada aberta"}
    }
  }
}
```

A API converte isso em `ComandoBorda` pendente. O Raspberry busca em `/api/edge/commands` e confirma em `/api/edge/commands/ack`.

Esse webhook e negado por padrao. Para aceitar comandos, configure `INTERSCITY_ENABLED=True` e envie o header `X-AutoPonto-Webhook-Token` com o mesmo valor de `INTERSCITY_WEBHOOK_SECRET`. A API tambem valida capacidade, tipo de comando, tamanho do payload, recurso ativo e `id` de origem para impedir replay que reabra comando ja entregue.

## Configuracao

Variaveis da API principal:

```env
INTERSCITY_ENABLED=False
INTERSCITY_BASE_URL=https://cidadesinteligentes.lsdi.ufma.br/interscity_lh
INTERSCITY_CATALOG_PATH=/catalog
INTERSCITY_DISCOVERY_PATH=/discovery
INTERSCITY_COLLECTOR_PATH=/collector
INTERSCITY_ADAPTOR_PATH=/adaptor
INTERSCITY_ACTUATOR_PATH=/actuator
INTERSCITY_TIMEOUT_SECONDS=5
INTERSCITY_WEBHOOK_SECRET=
```

O backend monta cada URL final como `INTERSCITY_BASE_URL + INTERSCITY_*_PATH`. Assim a base da instancia UFMA fica em um so lugar. Com `INTERSCITY_ENABLED=False`, a API principal continua funcionando sem depender da plataforma.

## Tolerancia A Falhas

Toda chamada ao Interscity passa pelo `ClienteInterSCity`, que usa timeout curto e retorna falha controlada. Erros no Catalog, Discovery, Collector, Adaptor ou Actuator nao bloqueiam login, CRUD academico, biometria, presenca, relatorios ou sincronizacao do edge.

O diagnostico administrativo fica em:

```http
GET /api/interscity/diagnostico/
```

Resposta exemplo:

```json
{
  "catalog": {"ok": true, "status": "ok"},
  "discovery": {"ok": false, "status": "timeout"},
  "collector": {"ok": false, "status": "erro_http", "codigo_http": 500},
  "adaptor": {"ok": false, "status": "indisponivel"},
  "actuator": {"ok": false, "status": "nao_configurado"}
}
```

Status possiveis:

- `ok`: servico respondeu.
- `timeout`: tempo limite excedido.
- `erro_http`: servico respondeu com erro HTTP.
- `indisponivel`: erro de rede, DNS ou conexao.
- `nao_configurado`: integracao desabilitada ou URL ausente.

## Escopo UFMA

O seed `seed_dados_ufma` cria um exemplo para Engenharia da Computacao UFMA Sao Luis, sem impedir o cadastro de outros cursos. As fontes de referencia usadas para o exemplo sao:

- Portal UFMA: https://portalpadrao.ufma.br/profissoes/nossos-centros-academicos/campus-sao-luis/saoluis-engenharia-da-computacao
- SIGAA UFMA: https://sigaa.ufma.br/sigaa/link/public/curso/curriculo/16827494
