# Diagramas Uteis Do Frontend

Estes diagramas ajudam a explicar o painel web do AutoPonto no TCC.

## 1. Organizacao Do Codigo

```mermaid
flowchart TB
    Front["autoponto-frontend/"]
    Main["src/main.tsx\nentrada React"]
    App["src/App.tsx\ntelas do MVP"]
    Api["src/api.ts\ncliente HTTP/JWT"]
    Types["src/types.ts\ntipos das respostas"]
    Styles["src/styles.css\nlayout visual"]
    Nginx["nginx.conf\nSPA + proxy /api"]

    Front --> Main
    Front --> Nginx
    Main --> App
    App --> Api
    App --> Types
    App --> Styles
```

## 2. Fluxo De Login

```mermaid
sequenceDiagram
    participant Usuario as Usuario
    participant Front as Frontend React
    participant API as Backend Django

    Usuario->>Front: Informa usuario e senha
    Front->>API: POST /api/auth/token/
    API-->>Front: access e refresh
    Front->>API: GET /api/me/
    API-->>Front: usuario, papel e permissoes
    Front-->>Usuario: Mostra painel conforme papel
```

## 3. Navegacao Por Papel

```mermaid
flowchart LR
    Login["Login"] --> Me["GET /api/me/"]
    Me --> Aluno["Painel do aluno"]
    Me --> Professor["Painel do professor"]
    Me --> Admin["Painel administrativo"]

    Aluno --> TurmasAluno["Turmas e presencas"]
    Aluno --> Biometria["Cadastro biometrico proprio"]

    Professor --> TurmasProfessor["Turmas ministradas"]
    Professor --> Relatorios["Relatorios de presenca"]

    Admin --> Cadastros["Usuarios, matriculas e vinculos"]
    Admin --> Diagnostico["Diagnostico Interscity"]
    Admin --> RelatoriosAdmin["Relatorios gerais"]
```

## 4. Fluxo De Relatorio Do Professor

```mermaid
sequenceDiagram
    participant Prof as Professor
    participant Front as Frontend
    participant API as Backend

    Prof->>Front: Seleciona turma e data
    Front->>API: GET /api/professor/turmas/
    API-->>Front: Turmas permitidas
    Front->>API: GET /api/relatorios/turmas/{id}/presencas/?data=YYYY-MM-DD
    API-->>Front: Presentes e ausentes
    Front->>API: GET /api/relatorios/turmas/{id}/resumo/?inicio=&fim=
    API-->>Front: Percentual por aluno
    Front-->>Prof: Tabelas de presenca
```

## 5. Cadastro Biometrico Pelo Aluno

```mermaid
sequenceDiagram
    participant Aluno as Aluno
    participant Front as Frontend
    participant API as Backend

    Aluno->>Front: Seleciona imagem do rosto
    Front->>Front: Converte arquivo para base64
    Front->>API: POST /api/me/biometria/
    API->>API: Gera embedding e verifica duplicidade
    API-->>Front: 201 criado ou 409 rosto duplicado
    Front-->>Aluno: Mensagem de sucesso ou conflito
```

## 6. Deploy Com Docker Compose

```mermaid
flowchart LR
    Browser["Navegador"] -->|"http://localhost:8080"| FrontNginx["frontend\nNginx"]
    FrontNginx -->|"arquivos estaticos"| SPA["React build"]
    FrontNginx -->|"proxy /api"| Backend["backend\nDjango/Gunicorn"]
    Backend --> DB["Postgres"]
    Backend -. opcional .-> InterSCity["Interscity UFMA"]
```

## Sugestao De Uso No Texto

- Use o diagrama 1 para explicar onde ficam os arquivos do frontend.
- Use os diagramas 2 e 3 para explicar autenticacao e autorizacao por papel.
- Use o diagrama 4 para justificar os relatorios do professor.
- Use o diagrama 5 para explicar a experiencia do cadastro biometrico.
- Use o diagrama 6 para apresentar o deploy integrado.
