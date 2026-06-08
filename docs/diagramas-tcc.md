# Diagramas Uteis Para O TCC

Este documento reune diagramas em Mermaid para explicar o AutoPonto no TCC. Eles foram escritos com os nomes atuais do codigo em portugues e podem ser renderizados no GitHub, VS Code ou em editores Mermaid.

## 1. Visao Geral Da Arquitetura

```mermaid
flowchart LR
    subgraph Sala["Sala De Aula"]
        ESP["DispositivoEsp32\n(camera/sensor local)"]
    end

    subgraph Borda["No De Borda - Raspberry Pi"]
        EdgeApp["edge-app\nsincronizacao e contexto"]
        FaceWorker["face-worker\nreconhecimento facial"]
        BancoLocal["Banco local/cache"]
    end

    subgraph Backend["API Principal AutoPonto"]
        API["Django REST API"]
        Dominio["Dominio academico\npresencas e biometria"]
        Banco["Banco principal"]
    end

    subgraph InterSCity["Interscity"]
        Catalog["Resource Catalog"]
        Adaptor["Resource Adaptor"]
        Collector["Data Collector"]
        Discovery["Resource Discovery"]
        Actuator["Actuator Controller"]
    end

    ESP -->|"frames e pedidos de contexto"| EdgeApp
    EdgeApp --> FaceWorker
    EdgeApp <--> BancoLocal
    EdgeApp -->|"pull, attendance, commands"| API
    API <--> Banco
    API --> Dominio
    API <--> Catalog
    API <--> Adaptor
    API <--> Collector
    API <--> Discovery
    API <--> Actuator
```

## 2. Topologia IoT

```mermaid
flowchart TB
    Campus["Campus"]
    Predio["Predio"]
    Sala1["Sala"]
    Sala2["Sala"]
    No["NoBorda\nRaspberry Pi"]
    Esp1["DispositivoEsp32"]
    Esp2["DispositivoEsp32"]

    Campus --> Predio
    Predio --> Sala1
    Predio --> Sala2
    No --> Esp1
    No --> Esp2
    Esp1 --> Sala1
    Esp2 --> Sala2
```

## 3. Entidade E Relacionamento Principal

```mermaid
erDiagram
    Campus ||--o{ Predio : possui
    Predio ||--o{ Sala : possui
    Campus ||--o{ Curso : oferece
    Curso ||--o{ Disciplina : possui
    PeriodoLetivo ||--o{ Turma : organiza
    Disciplina ||--o{ Turma : abre
    Turma ||--o{ MatriculaTurma : recebe
    Usuario ||--o{ MatriculaTurma : realiza
    Turma ||--o{ HorarioAula : possui
    Sala ||--o{ HorarioAula : aloca
    HorarioAula ||--o{ Aula : gera
    Aula ||--o{ RegistroPresenca : registra
    Usuario ||--o{ RegistroPresenca : recebe
    NoBorda ||--o{ DispositivoEsp32 : gerencia
    Sala ||--o{ DispositivoEsp32 : contem
    DispositivoEsp32 ||--o{ RegistroPresenca : registra
    DispositivoEsp32 ||--o{ EventoReconhecimento : produz
    Aula ||--o{ EventoReconhecimento : contextualiza
    Usuario ||--o{ EventoReconhecimento : candidato
    Usuario ||--|| PerfilBiometrico : possui
    PerfilBiometrico ||--o{ EmbeddingFacial : possui
    NoBorda ||--o{ ComandoBorda : recebe
    DispositivoEsp32 ||--o{ ComandoBorda : destino

    Usuario {
        uuid id PK
        string username
        string email
        string papel
        string matricula
        string nome_completo
    }

    Curso {
        uuid id PK
        string codigo
        string nome
        string turno
        int duracao_minima_periodos
        int duracao_maxima_periodos
        boolean ativo
    }

    Disciplina {
        uuid id PK
        string codigo
        string nome
        int carga_horaria
        int periodo_sugerido
        boolean obrigatoria
        boolean ativo
    }

    Turma {
        uuid id PK
        string codigo
        string nome
        boolean ativo
    }

    Aula {
        uuid id PK
        date data
        datetime inicio
        datetime fim
        string status
    }

    RegistroPresenca {
        uuid id PK
        string status
        datetime registrado_em
    }

    NoBorda {
        uuid id PK
        string codigo
        string nome
        boolean ativo
        datetime ultimo_sync_em
        string interscity_uuid
    }

    DispositivoEsp32 {
        uuid id PK
        string codigo
        string nome
        boolean ativo
        string versao_firmware
        string interscity_uuid
    }
```

## 4. Modelo Academico Simplificado

```mermaid
classDiagram
    class Campus {
        +nome
        +codigo
        +ativo
    }

    class Predio {
        +nome
        +codigo
        +ativo
    }

    class Sala {
        +nome
        +codigo
        +andar
        +capacidade
        +ativo
    }

    class Curso {
        +codigo
        +nome
        +turno
        +duracao_minima_periodos
        +duracao_maxima_periodos
        +ativo
    }

    class Disciplina {
        +codigo
        +nome
        +carga_horaria
        +periodo_sugerido
        +obrigatoria
        +ativo
    }

    class Turma {
        +codigo
        +nome
        +ativo
    }

    class HorarioAula {
        +dia_semana
        +horario_inicio
        +horario_fim
        +ativo
    }

    class Aula {
        +data
        +inicio
        +fim
        +status
    }

    Campus "1" --> "*" Predio
    Predio "1" --> "*" Sala
    Campus "1" --> "*" Curso
    Curso "1" --> "*" Disciplina
    Disciplina "1" --> "*" Turma
    Turma "1" --> "*" HorarioAula
    HorarioAula "1" --> "*" Aula
    Sala "1" --> "*" HorarioAula
```

## 5. Fluxo De Sincronizacao Do No

```mermaid
sequenceDiagram
    participant Edge as NoBorda Raspberry
    participant API as API AutoPonto
    participant DB as Banco Principal

    Edge->>API: GET /api/edge/pull?node_id=NO-CCET-01
    API->>DB: Busca DispositivoEsp32 do no
    API->>DB: Gera/consulta Aula da janela
    API->>DB: Busca alunos matriculados
    API->>DB: Busca EmbeddingFacial ativo
    API-->>Edge: data, deleted, cursors
    Edge->>Edge: Atualiza cache local
    Edge->>Edge: Distribui contexto para ESP32
```

## 6. Fluxo De Registro De Presenca

```mermaid
sequenceDiagram
    participant ESP as DispositivoEsp32
    participant Edge as NoBorda Raspberry
    participant Face as face-worker
    participant API as API AutoPonto
    participant DB as Banco Principal

    ESP->>Edge: Envia frame
    Edge->>Face: Solicita reconhecimento
    Face-->>Edge: aluno_id, score, aula_id
    Edge->>API: POST /api/edge/attendance
    API->>DB: Valida no, dispositivo e aula
    API->>DB: Valida MatriculaTurma ativa
    API->>DB: Upsert RegistroPresenca
    API->>DB: Cria EventoReconhecimento
    API-->>Edge: synced_ids
    Edge-->>ESP: Confirma processamento local
```

## 7. Fluxo De Matricula Biometrica

```mermaid
sequenceDiagram
    participant Admin as Administrador
    participant API as API AutoPonto
    participant Visao as GeradorEmbeddingVisao
    participant DB as Banco Principal

    Admin->>API: POST /api/perfis-biometricos/matricular/
    API->>API: Valida aluno e capturas
    API->>Visao: gerar_embedding(capturas)
    Visao-->>API: vetor e metadados
    API->>DB: Cria/ativa PerfilBiometrico
    API->>DB: Inativa embedding anterior
    API->>DB: Cria EmbeddingFacial ativo
    API-->>Admin: perfil e embedding
```

## 8. Fluxo De Comando Via Interscity

```mermaid
sequenceDiagram
    participant Actuator as Actuator Controller
    participant API as API AutoPonto
    participant DB as Banco Principal
    participant Edge as NoBorda Raspberry
    participant ESP as DispositivoEsp32

    Actuator->>API: POST /api/interscity/webhooks/actuator/
    API->>DB: Localiza recurso por interscity_uuid
    API->>DB: Cria ComandoBorda PENDENTE
    API-->>Actuator: command_id
    Edge->>API: GET /api/edge/commands
    API-->>Edge: commands
    Edge->>ESP: Encaminha comando local
    ESP-->>Edge: Resultado
    Edge->>API: POST /api/edge/commands/ack
    API->>DB: Marca ENTREGUE, FALHOU ou REJEITADO
```

## 9. Estados Da Aula

```mermaid
stateDiagram-v2
    [*] --> PLANEJADA
    PLANEJADA --> ABERTA: primeira presenca registrada
    ABERTA --> FECHADA: chamada encerrada
    PLANEJADA --> CANCELADA: aula cancelada
    ABERTA --> CANCELADA: cancelamento administrativo
    FECHADA --> [*]
    CANCELADA --> [*]
```

## 10. Estados Do Comando De Borda

```mermaid
stateDiagram-v2
    [*] --> PENDENTE
    PENDENTE --> ENTREGUE: ack DELIVERED
    PENDENTE --> FALHOU: ack FAILED
    PENDENTE --> REJEITADO: ack REJECTED
    FALHOU --> PENDENTE: reenvio administrativo
    ENTREGUE --> [*]
    REJEITADO --> [*]
```

## 11. Privacidade E Fronteiras De Dados

```mermaid
flowchart LR
    Capturas["Capturas base64\nsomente na requisicao"] --> API["API AutoPonto"]
    API --> Vetor["EmbeddingFacial.vetor\narmazenado no backend"]
    API --> Presenca["RegistroPresenca\nacademico canonico"]
    API --> Evento["EventoReconhecimento\nauditoria tecnica"]
    API --> Interscity["Interscity\ntelemetria anonima/agregavel"]

    Capturas -. "nao persiste" .-> Descarte["Descartadas apos processamento"]
    Vetor -. "nao enviar" .-> Interscity
    NomeAluno["Nome/matricula do aluno"] -. "nao enviar por padrao" .-> Interscity
```

## 12. Organizacao Do Codigo

```mermaid
flowchart TB
    URLs["api/urls.py\nrotas"]
    Views["api/views\ncamada HTTP"]
    Serializers["api/serializers\nvalidacao e JSON"]
    Services["api/services\nregras de negocio"]
    Models["api/models\ndominio e persistencia"]
    Tests["api/tests\ncontratos e regressao"]
    Docs["docs\ndocumentacao do TCC"]

    URLs --> Views
    Views --> Serializers
    Views --> Services
    Services --> Models
    Serializers --> Models
    Tests --> URLs
    Tests --> Services
    Docs -. explica .-> URLs
    Docs -. explica .-> Models
```

## Sugestao De Uso No Texto

- Use o diagrama 1 para apresentar a arquitetura geral.
- Use o diagrama 3 para explicar a modelagem do banco.
- Use os diagramas 5 e 6 para explicar a operacao normal do sistema.
- Use o diagrama 7 para explicar biometria e privacidade.
- Use o diagrama 8 para justificar a integracao com Interscity.
- Use os diagramas 9 e 10 se precisar explicar estados e robustez operacional.
