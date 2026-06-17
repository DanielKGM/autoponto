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
    Edge -->|"pull, attendance, status"| API["AutoPonto API\nDjango REST"]
    API <--> DB["PostgreSQL"]
    Edge -. "stats MQTT -> Resource Adaptor" .-> IC["Interscity UFMA"]
    Front["Frontend React"] --> API
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
    HorarioPadraoUFMA ||--o{ HorarioAula : padroniza
    Turma ||--o{ HorarioAula : possui
    Sala ||--o{ HorarioAula : aloca
    HorarioAula ||--o{ Aula : gera
    Aula ||--o{ RegistroPresenca : registra
    Usuario ||--o{ RegistroPresenca : recebe
    NoBorda ||--o{ DispositivoEsp32 : gerencia
    Sala ||--o{ DispositivoEsp32 : contem
    DispositivoEsp32 ||--o{ EventoReconhecimento : produz
    Aula ||--o{ EventoReconhecimento : contextualiza
    Usuario ||--|| PerfilBiometrico : possui
    PerfilBiometrico ||--o{ EmbeddingFacial : possui

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
        string status
        datetime fechada_em
    }

    DispositivoEsp32 {
        uuid id PK
        string codigo
        string status
        datetime status_atualizado_em
        string interscity_uuid
    }
```

## 3. Codigo UFMA Para Horarios

```mermaid
flowchart TD
    Codigo["Codigo SIGAA composto\n25M34"] --> Split["Normalizacao"]
    Split --> H1["HorarioPadraoUFMA\n2M34\nsegunda 10:00-11:40"]
    Split --> H2["HorarioPadraoUFMA\n5M34\nquinta 10:00-11:40"]
    H1 --> HA1["HorarioAula da turma"]
    H2 --> HA2["HorarioAula da turma"]
```

## 4. Fluxo De Pull

```mermaid
sequenceDiagram
    participant Edge as NoBorda
    participant API as API AutoPonto
    participant DB as PostgreSQL

    Edge->>API: GET /api/edge/pull
    API->>DB: Busca ESP32 e salas do no
    API->>DB: Materializa Aula pelo periodo de sync
    API->>DB: Busca alunos, matriculas e embeddings ativos
    API-->>Edge: locales, devices, lessons, students, enrollments, face_embeddings
    Edge->>Edge: Atualiza cache local
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
    Face-->>Edge: aluno_id, lesson_id, score
    Edge->>API: POST /api/edge/attendance
    API->>DB: Valida no, dispositivo, sala e matricula
    API->>DB: Valida Aula.inicio <= recognized_at <= Aula.fim
    API->>DB: Upsert RegistroPresenca
    API->>DB: Cria EventoReconhecimento sem imagem
    API-->>Edge: synced_ids
```

## 6. Status IoT E Interscity

```mermaid
sequenceDiagram
    participant ESP as ESP32
    participant MQTT as Mosquitto
    participant Edge as NoBorda
    participant API as API AutoPonto
    participant DB as PostgreSQL
    participant IC as Interscity
    participant Front as Dashboard

    ESP->>MQTT: sts/{device_id} = working
    MQTT->>Edge: status MQTT
    Edge->>Edge: Salva Redis device:{id}:status
    Edge->>API: POST /api/edge/devices/status/
    API->>DB: Atualiza DispositivoEsp32.status
    Edge-->>IC: Publica autoponto_device_stats
    Front->>API: GET status-dashboard
    API-->>Front: snapshot local
    PublicMap["Mapa publico futuro"]->>IC: consulta Collector/Discovery sob demanda
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
    API->>DB: Marca Aula como FECHADA
    API->>DB: Salva fechada_em e fechada_por
    Edge->>API: GET /api/edge/pull
    API-->>Edge: aula em deleted.lessons
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
    API->>DB: Inativa embedding anterior
    API->>DB: Salva novo EmbeddingFacial ativo
    API-->>Usuario: perfil e embedding
```

## 9. Estados Da Aula

```mermaid
stateDiagram-v2
    [*] --> PLANEJADA
    PLANEJADA --> ABERTA: primeira presenca aceita
    ABERTA --> FECHADA: professor/admin fecha
    PLANEJADA --> FECHADA: fechamento manual
    PLANEJADA --> CANCELADA: cancelamento
    ABERTA --> CANCELADA: cancelamento
    FECHADA --> [*]
    CANCELADA --> [*]
```

## 10. Estados Do Dispositivo

```mermaid
stateDiagram-v2
    [*] --> offline
    offline --> working: firmware publica status
    working --> idle: firmware ocioso
    idle --> working: novo processamento
    working --> offline: timeout sem status
    idle --> offline: timeout sem status
```

## 11. Privacidade

```mermaid
flowchart LR
    Capturas["Capturas base64\nsomente na requisicao"] --> API["API AutoPonto"]
    API --> Vetor["EmbeddingFacial.vetor"]
    API --> Presenca["RegistroPresenca"]
    API --> Evento["EventoReconhecimento\nsem frame bruto"]
    Edge["NoBorda"] -. "telemetria tecnica das ESP32" .-> IC["Interscity"]
    Capturas -. "descartadas" .-> Descarte["Sem persistencia"]
```

## Sugestao De Uso

- Arquitetura: diagrama 1.
- Banco/modelagem: diagramas 2 e 3.
- Operacao normal: diagramas 4 e 5.
- IoT/Interscity: diagrama 6.
- Fechamento manual: diagrama 7.
- Biometria, estados e privacidade: diagramas 8 a 11.
