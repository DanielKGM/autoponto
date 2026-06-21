# Prompt De Ajuste Do Edge-Node AutoPonto

Use este documento como prompt direto para adaptar `referencia-edge/autoponto-edgenode`. Nao edite os arquivos de referencia neste repositorio.

## Objetivo

Atualizar o edge-node para refletir a API principal como snapshot autoritativo do cache local:

- Nao existe entidade `MatriculaAula` na API principal.
- A API nao envia entidades completas no pull; ela envia `cache_redis` pronto para gravacao no Redis.
- `DispositivoEsp32.codigo` continua sendo o identificador usado pelo firmware/ESP32.
- `DispositivoEsp32.id` e o UUID usado em chamadas para a API principal.
- `dispositivos_por_codigo` e o mapa local `codigo -> id` usado para converter o `device_id` do firmware em UUID.
- O pull nao usa incremental, cursores, `deleted` nem msgpack.
- O edge deve substituir o snapshot Redis a cada pull.
- A sincronizacao e obrigatoria ao iniciar, na virada do dia e antes do inicio de cada aula salva no cache.

## Autenticacao

Manter:

```http
Authorization: NodeToken <token>
X-Node-Id: <codigo-ou-uuid-do-no>
```

Enviar tambem `node_id` na query/body quando o endpoint exigir.

## Pull Snapshot

Requisicao:

```http
GET /api/edge/pull?node_id=<node_id>
```

Resposta:

```json
{
  "snapshot_data": "2026-06-20",
  "synced_at": "2026-06-20T12:00:00Z",
  "cache_redis": {
    "dispositivos_por_codigo": {},
    "aulas_por_sala": {},
    "alunos_por_aula": {},
    "alunos_por_id": {},
    "embeddings_faciais": {}
  }
}
```

Regra do edge:

- Validar `snapshot_data`, `synced_at` e `cache_redis`.
- Chamar `substituir_snapshot_redis(cache_redis, snapshot_data, synced_at)`.
- Nao enviar `full=true`.
- Nao enviar `cursors`.
- Nao processar `deleted`.

## Estrutura Do `cache_redis`

`dispositivos_por_codigo`:

```json
{
  "ESP32-LAB101": {
    "dispositivo_id": "uuid-da-esp32-na-api",
    "dispositivo_codigo": "ESP32-LAB101",
    "sala_id": "uuid-da-sala",
    "ativo": true,
    "interscity_uuid": "uuid-interscity"
  }
}
```

`aulas_por_sala`:

```json
{
  "uuid-da-sala": [
    {
      "id": "uuid-da-aula",
      "nome": "Sistemas Embarcados - 01",
      "turma_id": "uuid-da-turma",
      "sala_id": "uuid-da-sala",
      "inicio": "2026-06-20T11:00:00Z",
      "fim": "2026-06-20T12:40:00Z",
      "status": "PLANEJADA"
    }
  ]
}
```

`alunos_por_aula`, `alunos_por_id` e `embeddings_faciais`:

```json
{
  "alunos_por_aula": {
    "uuid-da-aula": ["uuid-do-aluno"]
  },
  "alunos_por_id": {
    "uuid-do-aluno": {"nome": "Aluno Um"}
  },
  "embeddings_faciais": {
    "uuid-do-embedding": {
      "alunoId": "uuid-do-aluno",
      "embedding": {"dtype": "float32", "shape": [1, 3], "data": [0.1, 0.2, 0.3]}
    }
  }
}
```

Regra obrigatoria:

- Nao criar `MatriculaAula` como entidade do contrato.
- Para saber os alunos de uma aula no edge, consultar `aula:{aula_id}:alunos`, derivado de `alunos_por_aula`.
- Remocoes, cancelamentos e fechamentos desaparecem do Redis quando o snapshot seguinte substitui as chaves.

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
      "dispositivo_id": "uuid-da-esp32-na-api",
      "reconhecido_em": "2026-06-20T08:45:00-03:00",
      "score": 0.91
    }
  ]
}
```

Regras:

- `dispositivo_id` deve ser o UUID `dispositivos[].id`, nao o `codigo` do firmware.
- O backend aceita presenca somente se `reconhecido_em` estiver entre `aula.inicio` e `aula.fim`.
- A aula nao pode estar `FECHADA` nem `CANCELADA`.
- O aluno deve estar matriculado na turma da aula.
- O dispositivo deve pertencer ao no autenticado e estar na sala da aula.

## Politica De Sincronizacao

Nao depender de polling fixo de 60 segundos.

Politica recomendada:

- snapshot ao iniciar;
- snapshot na virada do dia;
- snapshot antes do inicio de cada aula salva no cache;
- envio de presencas pendentes depois do pull ou quando houver conectividade.

## IntersCity

- A API principal envia `dispositivos_por_codigo.*.interscity_uuid` no pull.
- O edge continua publicando telemetria das ESP32 no IntersCity por conta propria.
- Nao existem recursos IntersCity para `NoBorda`, apenas para ESP32.
