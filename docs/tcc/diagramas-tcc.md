# Diagramas Mermaid Para O TCC

Diagramas consolidados para Metodologia, Desenvolvimento do Prototipo e Analise
dos Resultados. Eles usam nomes de componentes e endpoints do codigo atual.

## 1. Casos De Uso

```mermaid
flowchart LR
    Aluno([Aluno])
    Professor([Professor])
    Admin([Administrador])
    Edge([EdgeNode])

    UCLogin((Autenticar-se))
    UCBio((Cadastrar biometria))
    UCFreq((Consultar frequencia))
    UCCalAluno((Consultar calendario))
    UCDashProf((Consultar dashboard docente))
    UCChamada((Acompanhar chamada))
    UCRelatorio((Gerar relatorio de presenca))
    UCCadAcad((Gerenciar modelo academico))
    UCCadIoT((Gerenciar nos e dispositivos))
    UCDiagIC((Diagnosticar InterSCity))
    UCPull((Baixar snapshot))
    UCAtt((Enviar eventos de presenca))

    Aluno --> UCLogin
    Aluno --> UCBio
    Aluno --> UCFreq
    Aluno --> UCCalAluno

    Professor --> UCLogin
    Professor --> UCDashProf
    Professor --> UCCalAluno
    Professor --> UCChamada
    Professor --> UCRelatorio

    Admin --> UCLogin
    Admin --> UCCadAcad
    Admin --> UCCadIoT
    Admin --> UCRelatorio
    Admin --> UCDiagIC

    Edge --> UCPull
    Edge --> UCAtt
```

## 2. Modelo De Dados Simplificado

```mermaid
erDiagram
    Usuario ||--o{ MatriculaTurma : aluno
    Usuario ||--o{ Turma : professor
    Usuario ||--o{ EmbeddingFacial : possui
    Campus ||--o{ Predio : possui
    Predio ||--o{ Sala : possui
    Campus ||--o{ Curso : oferece
    Curso ||--o{ Disciplina : possui
    PeriodoLetivo ||--o{ Turma : organiza
    Disciplina ||--o{ Turma : compoe
    Turma ||--o{ MatriculaTurma : possui
    Turma ||--o{ Aula : gera
    HorarioPadraoUFMA ||--o{ Aula : define
    Sala ||--o{ Aula : recebe
    Aula ||--o{ RegistroPresenca : possui
    Usuario ||--o{ RegistroPresenca : recebe
    NoBorda ||--o{ TokenNoBorda : autentica
    NoBorda ||--o{ DispositivoEsp32 : gerencia
    Sala ||--o{ DispositivoEsp32 : contem
    DispositivoEsp32 ||--o{ EventoReconhecimento : produz
    Aula ||--o{ EventoReconhecimento : contextualiza
    EmbeddingFacial ||--o{ EventoReconhecimento : referencia

    Usuario {
        uuid id PK
        string username
        string papel
        string matricula
    }

    Turma {
        uuid id PK
        string codigo
        uuid periodo_letivo_id FK
        uuid disciplina_id FK
    }

    Aula {
        uuid id PK
        date data
        datetime inicio
        datetime fim
        datetime fechada_em
        datetime cancelada_em
    }

    EmbeddingFacial {
        uuid id PK
        uuid aluno_id FK
        string versao_modelo
        json vetor
        string status
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

## 3. Fluxo De Cadastro Biometrico

```mermaid
sequenceDiagram
    participant Aluno as Aluno
    participant Front as Frontend React
    participant API as Backend Django
    participant CV as OpenCV YuNet/SFace
    participant Crypto as Fernet
    participant DB as PostgreSQL
    participant Redis as Redis

    Aluno->>Front: Seleciona capturas do rosto
    Front->>Front: Converte imagens para base64
    Front->>API: POST /api/me/biometria/
    API->>API: Valida quantidade, tamanho e formato
    API->>CV: Detecta face e gera embedding
    CV-->>API: Vetor facial + metadados
    API->>Redis: Lista embeddings ativos para comparar duplicidade
    API->>Crypto: Criptografa vetor facial
    API->>DB: Revoga embedding anterior e cria embedding ativo
    API->>Redis: Atualiza cache apos commit
    API-->>Front: 201 + identificador tecnico do embedding
    Front-->>Aluno: Exibe sucesso ou erro de validacao
```

## 4. Fluxo De Sincronizacao Servidor Para EdgeNode

```mermaid
sequenceDiagram
    participant Edge as EdgeNode
    participant API as Backend Django
    participant DB as PostgreSQL
    participant Crypto as Fernet
    participant Cache as Cache local do Edge

    Edge->>API: GET /api/edge/pull/
    API->>API: Autentica TokenNoBorda
    API->>DB: Busca dispositivos ativos do no
    API->>DB: Busca aulas validas do dia nas salas do no
    API->>DB: Busca matriculas, alunos e embeddings ativos
    API->>Crypto: Garante ciphertext dos embeddings
    API-->>Edge: snapshot_data, synced_at e cache_redis
    Edge->>Cache: Substitui dispositivos, aulas, alunos e embeddings
```

## 5. Fluxo De Envio De Presenca EdgeNode Para Servidor

```mermaid
sequenceDiagram
    participant ESP as ESP32-CAM
    participant Edge as EdgeNode
    participant Face as Worker facial
    participant API as Backend Django
    participant DB as PostgreSQL

    ESP->>Edge: Envia frame local
    Edge->>Face: Solicita reconhecimento facial
    Face-->>Edge: aluno_id, aula_id, dispositivo_id, score
    Edge->>API: POST /api/edge/attendance/
    API->>API: Autentica TokenNoBorda
    API->>DB: Valida dispositivo, aula, sala e aluno
    API->>DB: Confirma matricula ativa e janela da aula
    API->>DB: Upsert RegistroPresenca
    API->>DB: Cria EventoReconhecimento sem imagem bruta
    API-->>Edge: synced_ids
```

## 6. Arquitetura Backend, Frontend, PostgreSQL, Redis E InterSCity

```mermaid
flowchart LR
    Browser["Navegador"] --> Front["Frontend React/Vite"]
    Front -->|"REST /api"| API["Backend Django REST"]
    API --> DB["PostgreSQL"]
    API --> Redis["Redis\ncache biometrico"]
    API -.->|"Collector historico"| IC["InterSCity"]
    API -->|"JWT + cookie refresh"| Auth["Autenticacao"]
    Edge["EdgeNode"] -->|"GET /api/edge/pull"| API
    Edge -->|"POST /api/edge/attendance"| API
    ESP["ESP32-CAM"] -->|"frames locais"| Edge
    Edge -.->|"telemetria operacional"| IC
    Public["Mapa publico /mapa-iot"] --> Front
```

## 7. Mapa Publico E Telemetria InterSCity

```mermaid
sequenceDiagram
    participant Usuario as Usuario publico
    participant Front as PublicMapPage
    participant API as Backend Django
    participant DB as PostgreSQL
    participant IC as InterSCity Collector

    Usuario->>Front: Abre /mapa-iot
    Front->>API: GET /api/public/mapa/nos/
    API->>DB: Busca NoBorda com latitude/longitude e ESP32 ativos
    API-->>Front: Nos e dispositivos
    Usuario->>Front: Seleciona dispositivo
    Front->>API: GET /api/public/mapa/dispositivos/{id}/historico/
    API->>IC: POST /collector/resources/data ou /last
    IC-->>API: Capacidades tecnicas
    API-->>Front: Historico, ultimo valor e PIR em histograma
```

## 8. Pontos De Coleta De Metricas

```mermaid
flowchart TB
    Bio["Cadastro biometrico"] --> M1["biometria_cadastro_total_ms"]
    Bio --> M2["biometria_embedding_ms"]
    Bio --> M3["biometria_falha_deteccao_total"]
    Crypto["crypto_biometria.py"] --> M4["embedding_criptografia_ms"]
    Crypto --> M5["embedding_descriptografia_ms"]
    EdgePull["edge/pull"] --> M6["edge_snapshot_total_ms"]
    EdgeAttendance["edge/attendance"] --> M7["edge_attendance_total_ms"]
    FrontAPI["Endpoints principais"] --> M8["endpoint_*_ms"]
    IC["ClienteInterSCity"] --> M9["interscity_request_ms"]
    IC --> M10["interscity_falha_total"]
```

## 9. Estado Derivado Da Aula

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

## 10. Privacidade Do Fluxo Facial

```mermaid
flowchart LR
    Captura["Capturas base64\nsomente na requisicao"] --> API["Backend"]
    API --> CV["Detector e reconhecedor facial"]
    CV --> Emb["Embedding numerico"]
    Emb --> Crypto["Criptografia Fernet"]
    Crypto --> DB["EmbeddingFacial.vetor criptografado"]
    DB --> Edge["Snapshot EdgeNode com ciphertext"]
    Captura -. "nao persistida" .-> Descarte["Descarte apos processamento"]
    Edge --> Presenca["RegistroPresenca e EventoReconhecimento\nsem frame bruto"]
```
