# Prompt De Ajuste Do Edge-Node AutoPonto

Use este documento como prompt direto para adaptar `referencia-edge/autoponto-edgenode`.
Nao edite os arquivos de referencia neste repositorio.

## Objetivo

Atualizar o edge-node para refletir a API principal como cache local:

- Todos os campos `id` vindos da API principal sao UUID.
- Nao existe entidade `MatriculaAula` na API principal.
- A API envia `aulas` com `turma_id` e `matriculas_turma` com `turma_id` + `aluno_id`.
- O edge deve derivar localmente quais alunos pertencem a uma aula cruzando `aula.turma_id` com `matriculas_turma.turma_id`.
- `DispositivoEsp32.codigo` continua sendo o identificador usado pelo firmware/ESP32.
- `DispositivoEsp32.id` e o UUID usado em chamadas para a API principal.
- O edge deve manter um mapa local `codigo -> id` para converter o `device_id` do firmware em UUID.
- Full sync e obrigatorio ao iniciar, na virada do dia e antes do inicio de cada aula.
- O incremental usa cursores por entidade/data, salvos em `sync_state(entity, cursor)`.

## Autenticacao

Manter:

```http
Authorization: NodeToken <token>
X-Node-Id: <codigo-ou-uuid-do-no>
```

Enviar tambem `node_id` na query/body quando o endpoint exigir.

## Pull Completo

Requisicao:

```http
GET /api/edge/pull?node_id=<node_id>&full=true
```

Resposta:

```json
{
  "full": true,
  "full_required": false,
  "data": {
    "salas": [],
    "dispositivos": [],
    "aulas": [],
    "alunos": [],
    "matriculas_turma": [],
    "embeddings_faciais": []
  },
  "deleted": {
    "salas": [],
    "dispositivos": [],
    "aulas": [],
    "alunos": [],
    "matriculas_turma": [],
    "embeddings_faciais": []
  },
  "cursors": {
    "salas": "2026-06-20T12:00:00Z",
    "dispositivos": "2026-06-20T12:00:00Z",
    "aulas": "2026-06-20T12:00:00Z",
    "alunos": "2026-06-20T12:00:00Z",
    "matriculas_turma": "2026-06-20T12:00:00Z",
    "embeddings_faciais": "2026-06-20T12:00:00Z"
  }
}
```

Regra do edge:

- Substituir o cache local pelas listas de `data`.
- Guardar cada item de `cursors` em `sync_state(entity, cursor)`.
- `deleted` normalmente vem vazio no full sync.
- Usar exatamente `full=true`. Nao enviar `full=1`, `full=yes`, `full=sim` ou variantes.

## Pull Incremental

Requisicao:

```http
GET /api/edge/pull?node_id=<node_id>&cursors=<msgpack-hex>
```

`cursors` e um msgpack em hexadecimal com um objeto por entidade:

```json
{
  "salas": "2026-06-20T12:00:00Z",
  "dispositivos": "2026-06-20T12:00:00Z",
  "aulas": "2026-06-20T12:00:00Z",
  "alunos": "2026-06-20T12:00:00Z",
  "matriculas_turma": "2026-06-20T12:00:00Z",
  "embeddings_faciais": "2026-06-20T12:00:00Z"
}
```

Regra do edge:

- Aplicar `data.*` como upsert no cache local.
- Aplicar `deleted.*` como remocao local por UUID.
- Atualizar os cursores locais com `cursors` da resposta.
- Se algum cursor local for perdido, enviar `full=true` para reconstruir o cache.

Exemplo de resposta incremental:

```json
{
  "full": false,
  "full_required": false,
  "data": {
    "salas": [],
    "dispositivos": [],
    "aulas": [],
    "alunos": [],
    "matriculas_turma": [],
    "embeddings_faciais": []
  },
  "deleted": {
    "salas": [],
    "dispositivos": [],
    "aulas": [],
    "alunos": [],
    "matriculas_turma": [],
    "embeddings_faciais": []
  },
  "cursors": {
    "salas": "2026-06-20T12:05:00Z",
    "dispositivos": "2026-06-20T12:05:00Z",
    "aulas": "2026-06-20T12:05:00Z",
    "alunos": "2026-06-20T12:05:00Z",
    "matriculas_turma": "2026-06-20T12:05:00Z",
    "embeddings_faciais": "2026-06-20T12:05:00Z"
  }
}
```

## Payloads Principais

Dispositivo:

```json
{
  "id": "uuid-da-esp32-na-api",
  "codigo": "ESP32-LAB101",
  "sala_id": "uuid-da-sala",
  "ativo": true,
  "interscity_uuid": "uuid-interscity"
}
```

Aula:

```json
{
  "id": "uuid-da-aula",
  "nome": "Sistemas Embarcados - 01",
  "turma_id": "uuid-da-turma",
  "sala_id": "uuid-da-sala",
  "inicio": "2026-06-20T11:00:00Z",
  "fim": "2026-06-20T12:40:00Z",
  "status": "PLANEJADA"
}
```

Matricula em turma:

```json
{
  "id": "uuid-da-matricula-turma",
  "turma_id": "uuid-da-turma",
  "aluno_id": "uuid-do-aluno"
}
```

Regra obrigatoria:

- Nao criar `MatriculaAula` como entidade do contrato.
- Para saber os alunos de uma aula: selecionar `matriculas_turma` em que `turma_id == aula.turma_id`.
- Remover matriculas por UUID quando aparecerem em `deleted.matriculas_turma`.

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

## Politica De Sincronizacao Recomendada

Nao depender de polling fixo de 60 segundos.

Politica recomendada:

- full sync ao iniciar;
- full sync na virada do dia;
- full sync antes do inicio da aula;
- incremental opcional em intervalo maior com jitter;

## IntersCity

- A API principal envia `dispositivos[].interscity_uuid` no pull.
- O edge continua publicando telemetria das ESP32 no IntersCity por conta propria.
- Nao existem recursos IntersCity para `NoBorda`, apenas para ESP32.
