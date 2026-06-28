# Diagramas Uteis Do Frontend

Estes diagramas ajudam a explicar o painel web do AutoPonto no TCC.

## 1. Organizacao Do Codigo

```mermaid
flowchart TB
    Front["autoponto-frontend/"]
    Main["src/main.tsx\nentrada React"]
    App["src/app/App.tsx\nrotas"]
    Nav["src/app/navigation.ts\nmenus por permissao"]
    Shell["src/shell/\nlayout autenticado"]
    Api["src/shared/api.ts\ncliente HTTP/JWT"]
    Types["src/shared/types.ts\ntipos das respostas"]
    UI["src/shared/ui/\ncomponentes"]
    Styles["src/scss/v4/\nlayout visual"]
    Nginx["nginx.conf\nSPA + proxy /api"]

    Front --> Main
    Front --> Nginx
    Main --> App
    App --> Nav
    App --> Shell
    App --> Api
    App --> Types
    App --> UI
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
    API-->>Front: access no JSON + refresh em cookie HttpOnly
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
    Me --> Perfil["Perfil"]
    Me --> MapaAuth["Mapa IoT autenticado"]

    Aluno --> DashboardAluno["Dashboard e frequencia"]
    Aluno --> CalendarioAluno["Calendario"]
    Aluno --> Biometria["Biometria propria"]

    Professor --> DashboardProfessor["Chamadas e turmas"]
    Professor --> CalendarioProfessor["Calendario"]
    Professor --> DetalheAula["Detalhe de aula/turma"]

    Admin --> Academico["Academico e vinculos"]
    Admin --> IoT["Nos, ESP32 e diagnostico"]
    Admin --> RelatoriosAdmin["Aulas e relatorios"]
```

## 4. Fluxo De Relatorio Do Professor

```mermaid
sequenceDiagram
    participant Prof as Professor
    participant Front as Frontend
    participant API as Backend

    Prof->>Front: Abre dashboard ou detalhe de turma
    Front->>API: GET /api/professor/dashboard/
    API-->>Front: Chamadas abertas, pendentes e turmas
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
    Front->>API: GET /api/me/biometrias/
    API-->>Front: Biometrias ativas e revogadas
    Front-->>Aluno: Mensagem de sucesso ou conflito
```

## 6. Mapa IoT Publico

```mermaid
sequenceDiagram
    participant Usuario as Usuario
    participant Front as PublicMapPage
    participant API as Backend Django
    participant IC as IntersCity Collector

    Usuario->>Front: Abre /mapa-iot
    Front->>API: GET /api/public/mapa/nos/
    API-->>Front: Nos com coordenadas e ESP32
    Usuario->>Front: Seleciona dispositivo
    Front->>API: GET /api/public/mapa/dispositivos/{id}/historico/?periodo=7d
    API->>IC: POST /collector/resources/data
    IC-->>API: Historico de capacidades
    API-->>Front: Historico + ultimo + PIR histograma
```

## 7. Deploy Com Docker Compose

```mermaid
flowchart LR
    Browser["Navegador"] -->|"http://localhost:8080"| FrontNginx["frontend\nNginx"]
    FrontNginx -->|"arquivos estaticos"| SPA["React build"]
    FrontNginx -->|"proxy /api"| Backend["backend\nDjango/Gunicorn"]
    Backend --> DB["Postgres"]
    Backend --> Redis["Redis\ncache biometrico"]
    Backend -. historico .-> InterSCity["Interscity Collector"]
```

## Sugestao De Uso No Texto

- Use o diagrama 1 para explicar onde ficam os arquivos do frontend.
- Use os diagramas 2 e 3 para explicar autenticacao e autorizacao por papel.
- Use o diagrama 4 para justificar dashboard, detalhe de turma e relatorios do professor.
- Use o diagrama 5 para explicar a experiencia do cadastro biometrico.
- Use o diagrama 6 para explicar mapa publico e historico IoT.
- Use o diagrama 7 para apresentar o deploy integrado.
