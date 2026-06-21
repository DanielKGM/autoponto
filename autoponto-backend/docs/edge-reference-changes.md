# Prompt De Ajuste Do Edge-Node AutoPonto

Use este documento como prompt direto para adaptar `referencia-edge/autoponto-edgenode`. Nao edite os arquivos de referencia neste repositorio.

## Objetivo

Atualizar o edge-node para refletir a API principal como snapshot autoritativo do cache local:

- Todos os campos `id` vindos da API principal sao UUID.
- Nao existe entidade `MatriculaAula` na API principal.
- A API envia `aulas` com `turma_id` e `matriculas_turma` com `turma_id` + `aluno_id`.
- O edge deve derivar localmente quais alunos pertencem a uma aula cruzando `aula.turma_id` com `matriculas_turma.turma_id`.
- `DispositivoEsp32.codigo` continua sendo o identificador usado pelo firmware/ESP32.
- `DispositivoEsp32.id` e o UUID usado em chamadas para a API principal.
- O edge deve manter um mapa local `codigo -> id` para converter o `device_id` do firmware em UUID.
- O pull nao usa incremental, cursores, `deleted` nem msgpack.
- O edge deve substituir o cache local replicado a cada pull.
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
  "data": {
    "salas": [],
    "dispositivos": [],
    "aulas": [],
    "alunos": [],
    "matriculas_turma": [],
    "embeddings_faciais": []
  },
  "synced_at": "2026-06-20T12:00:00Z"
}
```

Regra do edge:

- Limpar as tabelas locais replicadas antes de aplicar o payload.
- Inserir as listas recebidas em `data`.
- Reconstruir o cache Redis de reconhecimento depois de aplicar o snapshot.
- Nao enviar `full=true`.
- Nao enviar `cursors`.
- Nao manter tabela `sync_state`.
- Nao processar `deleted`.

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
- Remocoes, cancelamentos e fechamentos desaparecem do cache quando o snapshot seguinte substitui as tabelas locais.

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

- A API principal envia `dispositivos[].interscity_uuid` no pull.
- O edge continua publicando telemetria das ESP32 no IntersCity por conta propria.
- Nao existem recursos IntersCity para `NoBorda`, apenas para ESP32.
