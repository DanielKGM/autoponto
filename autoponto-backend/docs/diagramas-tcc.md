# Diagramas Uteis Para O TCC

Diagramas em Mermaid para explicar o MVP AutoPonto. Eles usam os nomes atuais do codigo em portugues.

## 1. Visao Geral Da Arquitetura

```mermaid
flowchart LR
    subgraph SalaAula["Sala de aula"]
        ESP["DispositivoEsp32\ncamera/sensor"]
    end

    subgraph Borda["NoBorda - Raspberry Pi"]
        Edge["edge-app\ncontexto e sync"]
        Face["face-worker\nreconhecimento"]
        Cache["cache local"]
    end

    subgraph Backend["AutoPonto Backend"]
        API["Django REST API"]
        DB["PostgreSQL"]
        Dominio["frequencia\nbiometria\nrelatorios"]
    end

    subgraph InterSCity["Interscity UFMA opcional"]
        Catalog["Catalog"]
        Discovery["Discovery"]
        Collector["Collector"]
        Adaptor["Adaptor"]
        Actuator["Actuator"]
    end

    ESP -->|"frames"| Edge
    Edge --> Face
    Edge <--> Cache
    Edge <--> |"pull, attendance, commands"| API
    API <--> DB
    API --> Dominio
    API -.-> Catalog
    API -.-> Discovery
    API -.-> Collector
    API -.-> Adaptor
    API -.-> Actuator
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
    NoBorda ||--o{ ComandoBorda : recebe
    DispositivoEsp32 ||--o{ ComandoBorda : destino
    Usuario ||--o{ ComandoBorda : cria

    Usuario {
        uuid id PK
        string username
        string email
        string papel
        string matricula
        string nome_completo
    }

    HorarioAula {
        uuid id PK
        int dia_semana
        time horario_inicio
        time horario_fim
        int abre_chamada_minutos
        int fecha_chamada_minutos
        boolean ativo
    }

    Aula {
        uuid id PK
        date data
        datetime inicio
        datetime fim
        datetime chamada_inicio
        datetime chamada_fim
        string status
        datetime fechada_em
    }

    RegistroPresenca {
        uuid id PK
        string status
        datetime registrado_em
    }

    ComandoBorda {
        uuid id PK
        string tipo
        json payload
        string status
        string origem
        string capacidade
    }
```

## 3. Modelo Academico Enxuto

```mermaid
classDiagram
    class Campus {
        +nome
        +codigo
        +ativo
    }
    class Predio {
        +campus
        +nome
        +codigo
        +ativo
    }
    class Sala {
        +predio
        +nome
        +codigo
        +ativo
    }
    class Curso {
        +campus
        +codigo
        +nome
        +ativo
    }
    class Disciplina {
        +curso
        +codigo
        +nome
        +ativo
    }
    class Turma {
        +periodo_letivo
        +disciplina
        +codigo
        +professores
        +ativo
    }
    class MatriculaTurma {
        +turma
        +aluno
        +ativo
    }

    Campus --> Predio
    Predio --> Sala
    Campus --> Curso
    Curso --> Disciplina
    Disciplina --> Turma
    Turma --> MatriculaTurma
```

## 4. Janela De Chamada

```mermaid
sequenceDiagram
    participant Admin as Professor/Admin
    participant API as API AutoPonto
    participant DB as PostgreSQL

    Admin->>API: POST /api/horarios-aula/{id}/definir-janela-chamada/
    API->>DB: Atualiza HorarioAula.abre/fecha_chamada_minutos
    API->>DB: Recalcula aulas futuras nao fechadas/canceladas
    API-->>Admin: horario atualizado e total de aulas recalculadas
```

## 5. Fechamento Manual Da Chamada

```mermaid
sequenceDiagram
    participant Professor as Professor
    participant API as API AutoPonto
    participant DB as PostgreSQL
    participant Edge as NoBorda

    Professor->>API: POST /api/aulas/{id}/fechar-chamada/
    API->>DB: Verifica professor da turma
    API->>DB: Marca Aula como FECHADA
    API->>DB: Salva fechada_em e fechada_por
    Edge->>API: GET /api/edge/pull
    API-->>Edge: aula fechada em deleted.lessons
```

## 6. Fluxo De Sincronizacao Do No

```mermaid
sequenceDiagram
    participant Edge as NoBorda Raspberry
    participant API as API AutoPonto
    participant DB as PostgreSQL

    Edge->>API: GET /api/edge/pull?node_id=NO-CCET-01
    API->>DB: Busca DispositivoEsp32 do no
    API->>DB: Materializa Aula na janela configurada
    API->>DB: Busca MatriculaTurma e EmbeddingFacial ativos
    API-->>Edge: lessons com attendance_starts_at e attendance_ends_at
    Edge->>Edge: Atualiza cache local
```

## 7. Fluxo De Registro De Presenca

```mermaid
sequenceDiagram
    participant ESP as DispositivoEsp32
    participant Edge as NoBorda
    participant Face as face-worker
    participant API as API AutoPonto
    participant DB as PostgreSQL

    ESP->>Edge: Envia frame
    Edge->>Face: Reconhecimento facial
    Face-->>Edge: aluno_id, lesson_id, score
    Edge->>API: POST /api/edge/attendance
    API->>DB: Valida no, dispositivo, sala e matricula
    API->>DB: Valida janela chamada_inicio/chamada_fim
    API->>DB: Upsert RegistroPresenca
    API->>DB: Cria EventoReconhecimento sem imagem/payload bruto
    API-->>Edge: synced_ids
```

## 8. Fluxo De Biometria

```mermaid
sequenceDiagram
    participant Usuario as Aluno/Admin
    participant API as API AutoPonto
    participant Visao as OpenCV YuNet/SFace
    participant DB as PostgreSQL

    Usuario->>API: POST biometria com capturas base64
    API->>Visao: gerar_embedding(capturas)
    Visao-->>API: vetor
    API->>DB: Compara com embeddings ativos de outros alunos
    API->>DB: Inativa embedding anterior
    API->>DB: Salva novo EmbeddingFacial ativo
    API-->>Usuario: perfil e embedding
```

## 9. Fluxo De Comando

```mermaid
sequenceDiagram
    participant Admin as Admin/Interscity
    participant API as API AutoPonto
    participant DB as PostgreSQL
    participant Edge as NoBorda
    participant ESP as DispositivoEsp32

    Admin->>API: Cria comando
    API->>DB: Salva ComandoBorda PENDENTE
    Edge->>API: GET /api/edge/commands
    API-->>Edge: commands
    Edge->>ESP: Encaminha comando local
    ESP-->>Edge: Resultado
    Edge->>API: POST /api/edge/commands/ack
    API->>DB: Marca ENTREGUE, FALHOU ou REJEITADO
```

## 10. Estados

```mermaid
stateDiagram-v2
    [*] --> PLANEJADA
    PLANEJADA --> ABERTA: primeira presenca aceita
    ABERTA --> FECHADA: professor/admin fecha
    PLANEJADA --> FECHADA: fechamento manual sem presenca
    PLANEJADA --> CANCELADA: cancelamento
    ABERTA --> CANCELADA: cancelamento
    FECHADA --> [*]
    CANCELADA --> [*]
```

```mermaid
stateDiagram-v2
    [*] --> PENDENTE
    PENDENTE --> ENTREGUE: ack DELIVERED
    PENDENTE --> FALHOU: ack FAILED
    PENDENTE --> REJEITADO: ack REJECTED
```

## 11. Privacidade

```mermaid
flowchart LR
    Capturas["Capturas base64\nsomente na requisicao"] --> API["API AutoPonto"]
    API --> Vetor["EmbeddingFacial.vetor"]
    API --> Presenca["RegistroPresenca"]
    API --> Evento["EventoReconhecimento\nsem frame bruto"]
    API -. "nao envia por padrao" .-> InterSCity["Interscity"]
    Capturas -. "descartadas" .-> Descarte["Sem persistencia"]
```

## Sugestao De Uso No Texto

- Arquitetura: diagrama 1.
- Banco/modelagem: diagramas 2 e 3.
- Janela e fechamento de chamada: diagramas 4 e 5.
- Operacao normal do sistema: diagramas 6 e 7.
- Biometria e privacidade: diagramas 8 e 11.
- Comandos e Interscity: diagrama 9.
