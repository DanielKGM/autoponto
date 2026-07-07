# Diagramas Uteis Para O TCC

Diagramas em Mermaid para explicar o MVP AutoPonto.

## 1. Arquitetura Geral

```mermaid
flowchart LR
    ESP["ESP32\ncamera + firmware"] -->|"frames HTTP local"| Edge["NoBorda Raspberry\nedge-app"]
    ESP -->|"sts/{device_id} MQTT"| MQTT["Mosquitto local"]
    MQTT --> Edge
    Edge --> Face["face-worker\nYuNet/SFace"]
    Edge <--> Cache["SQLite/Redis local"]
    Edge -->|"pull, attendance"| API["AutoPonto API\nDjango REST"]
    API <--> DB["PostgreSQL"]
    Edge -. "status/logs -> Resource Adaptor" .-> IC["Interscity UFMA"]
    Front["Frontend React"] --> API
    Public["Mapa publico"] --> API
    API -. "historico Collector" .-> IC
```

## 2. Entidade E Relacionamento Principal

```mermaid
erDiagram
    Campus ||--o{ Predio : possui
    Predio ||--o{ Sala : possui
    Campus ||--o{ Curso : oferece
    Curso ||--o{ Disciplina : possui
    PeriodoLetivo ||--o{ Turma : organiza
    Disciplina ||--o{ Turma : abre
    Usuario ||--o{ Turma : ministra
    Turma ||--o{ MatriculaTurma : recebe
    Usuario ||--o{ MatriculaTurma : realiza
    HorarioPadraoUFMA ||--o{ Aula : padroniza
    Turma ||--o{ Aula : possui
    Sala ||--o{ Aula : aloca
    Aula ||--o{ RegistroPresenca : registra
    Usuario ||--o{ RegistroPresenca : recebe
    NoBorda ||--o{ DispositivoEsp32 : gerencia
    Sala ||--o{ DispositivoEsp32 : contem
    DispositivoEsp32 ||--o{ EventoReconhecimento : produz
    Aula ||--o{ EventoReconhecimento : contextualiza
    Usuario ||--o{ EmbeddingFacial : possui

    HorarioPadraoUFMA {
        uuid id PK
        string codigo
        int dia_semana
        time horario_inicio
        time horario_fim
        boolean ativo
    }

    Aula {
        uuid id PK
        date data
        datetime inicio
        datetime fim
        datetime cancelada_em
        datetime fechada_em
    }

    NoBorda {
        uuid id PK
        string codigo
        decimal latitude
        decimal longitude
    }

    DispositivoEsp32 {
        uuid id PK
        string codigo
        string interscity_uuid
    }
```

## 3. Codigo UFMA Para Horarios

```mermaid
flowchart TD
    Codigo["Codigo SIGAA composto\n25M34"] --> Split["Normalizacao"]
    Split --> H1["HorarioPadraoUFMA\n2M34\nsegunda 10:00-11:40"]
    Split --> H2["HorarioPadraoUFMA\n5M34\nquinta 10:00-11:40"]
    H1 --> A1["Aulas materializadas da turma"]
    H2 --> A2["Aulas materializadas da turma"]
```

## 4. Fluxo De Pull

```mermaid
sequenceDiagram
    participant Edge as NoBorda
    participant API as API AutoPonto
    participant DB as PostgreSQL

    Edge->>API: GET /api/edge/pull
    API->>DB: Busca ESP32 e salas do no
    API->>DB: Busca aulas ja materializadas do dia
    API->>DB: Anota status derivado e filtra aulas validas
    API->>DB: Busca alunos, matriculas e embeddings ativos
    API-->>Edge: snapshot_data + synced_at + cache_redis
    Edge->>Edge: Substitui chaves Redis do snapshot
```

## 5. Fluxo De Presenca

```mermaid
sequenceDiagram
    participant ESP as ESP32
    participant Edge as NoBorda
    participant Face as face-worker
    participant API as API AutoPonto
    participant DB as PostgreSQL

    ESP->>Edge: Envia frame
    Edge->>Face: Reconhecimento facial
    Face-->>Edge: aluno_id, aula_id, score
    Edge->>API: POST /api/edge/attendance
    API->>DB: Valida no, dispositivo, sala e matricula
    API->>DB: Valida Aula.inicio <= reconhecido_em < Aula.fim
    API->>DB: Upsert RegistroPresenca
    API->>DB: Cria EventoReconhecimento sem imagem
    API-->>Edge: synced_ids
```

## 6. Interscity E Mapa Publico

```mermaid
sequenceDiagram
    participant ESP as ESP32
    participant MQTT as Mosquitto
    participant Edge as NoBorda
    participant API as API AutoPonto
    participant IC as Interscity
    participant Front as Mapa publico

    Edge->>API: GET /api/edge/pull
    API-->>Edge: dispositivos com interscity_uuid
    Edge->>MQTT: cmd/{device_id} {"stats": true}
    ESP->>MQTT: log/{device_id}
    MQTT->>Edge: status, presenca, rssi, heap/psram, lesson, remaining_ms, next_ms
    Edge-->>IC: POST /adaptor/resources/{uuid}/data
    Front->>API: GET /api/public/mapa/nos/
    API-->>Front: Nos com latitude/longitude + ESP32
    Front->>API: GET /api/public/mapa/dispositivos/{id}/historico/?periodo=7d
    API->>IC: POST /collector/resources/data
    IC-->>API: historico filtrado
    API-->>Front: historico + ultimo valor + PIR histograma
```

## 7. Fechamento Manual

```mermaid
sequenceDiagram
    participant Professor as Professor/Admin
    participant API as API AutoPonto
    participant DB as PostgreSQL
    participant Edge as NoBorda

    Professor->>API: POST /api/aulas/{id}/fechar-chamada/
    API->>DB: Verifica acesso a turma
    API->>DB: Preenche fechada_em e fechada_por
    Edge->>API: GET /api/edge/pull
    API-->>Edge: cache_redis sem aula fechada/cancelada
    Edge->>Edge: Substitui chaves Redis do snapshot
```

## 8. Biometria

```mermaid
sequenceDiagram
    participant Usuario as Aluno/Admin
    participant API as API AutoPonto
    participant Visao as OpenCV YuNet/SFace
    participant DB as PostgreSQL

    Usuario->>API: POST biometria com capturas base64
    API->>Visao: gerar_embedding(capturas)
    Visao-->>API: vetor SFace
    API->>DB: Compara com embeddings ativos
    API->>DB: Revoga embeddings ativos anteriores
    API->>DB: Cria novo EmbeddingFacial ativo criptografado
    API-->>Usuario: embedding ativo
```

## 9. Status Derivado Da Aula

```mermaid
stateDiagram-v2
    [*] --> PLANEJADA
    PLANEJADA --> ABERTA: inicio <= agora < fim
    ABERTA --> FECHADA: fim <= agora
    PLANEJADA --> FECHADA: fim <= agora
    ABERTA --> FECHADA: professor/admin preenche fechada_em
    PLANEJADA --> CANCELADA: cancelada_em preenchido
    ABERTA --> CANCELADA: cancelada_em preenchido
    FECHADA --> [*]
    CANCELADA --> [*]
```

## 10. Privacidade

```mermaid
flowchart LR
    Capturas["Capturas base64\nsomente na requisicao"] --> API["API AutoPonto"]
    API --> Vetor["EmbeddingFacial.vetor\ncriptografado"]
    API --> Presenca["RegistroPresenca"]
    API --> Evento["EventoReconhecimento\nsem frame bruto"]
    Edge["NoBorda"] -. "telemetria tecnica das ESP32" .-> IC["Interscity"]
    Mapa["Mapa publico"] -. "historico operacional filtrado" .-> APIMapa["API publica"]
    Capturas -. "descartadas" .-> Descarte["Sem persistencia"]
```

## Sugestao De Uso

- Arquitetura: diagrama 1.
- Banco/modelagem: diagramas 2 e 3.
- Operacao normal: diagramas 4 e 5.
- IoT/Interscity e mapa publico: diagrama 6.
- Fechamento manual: diagrama 7.
- Biometria, estados e privacidade: diagramas 8 a 10.
