# Paginas E Fluxos Do Frontend

Este documento descreve a estrutura atual do frontend React/Vite e os fluxos demonstraveis no MVP do TCC.

## Estrutura

- `src/app/App.tsx`: shell autenticado, navegacao por area e logout.
- `src/features/auth/LoginScreen.tsx`: login com JWT e refresh via cookie HttpOnly.
- `src/features/aluno/AlunoPainel.tsx`: turmas, presencas e cadastro biometrico proprio.
- `src/features/professor/ProfessorPainel.tsx`: relatorios por data e resumo da turma.
- `src/features/admin/AdminPainel.tsx`: orquestra abas administrativas.
- `src/features/admin/CadastrosAcademicos.tsx`: campus, predio, sala, periodo, curso, disciplina, turma e horarios.
- `src/features/admin/VinculosAcademicos.tsx`: matricula aluno-turma e vinculo professor-turma.
- `src/features/admin/InfraestruturaIot.tsx`: no de borda, ESP32, diagnostico IntersCity e mapa operacional.
- `src/features/admin/BiometriaAdmin.tsx`: cadastro biometrico de aluno pelo administrador.
- `src/features/mapa/MapaOperacional.tsx`: visao de dispositivos e ultimo snapshot local.
- `src/features/perfil/PerfilPainel.tsx`: dados da conta autenticada.
- `src/components`: componentes pequenos reutilizaveis.
- `src/shared`: formatacao e biometria no cliente.

O arquivo antigo `src/App.tsx` foi removido. O ponto de entrada `src/main.tsx` importa diretamente `src/app/App.tsx`.

## Fluxo De Administrador

1. Entra com usuario administrador.
2. Acessa `Admin`.
3. Em `Resumo`, cadastra usuarios basicos sem email obrigatorio.
4. Em `Academico`, cadastra a estrutura fisica e academica: campus, predios, salas, periodos, cursos, disciplinas, turmas e horarios UFMA.
5. Em `Vinculos`, matricula alunos em turmas e vincula professores.
6. Em `IoT`, cadastra no de borda e ESP32, confere status local e diagnostico IntersCity.
7. Em `Biometria`, cadastra o rosto de um aluno.
8. Em `Relatorios`, consulta presencas da turma com a mesma tela usada pelo professor.

## Fluxo De Professor

1. Entra com usuario professor.
2. Acessa `Professor`.
3. Seleciona turma e data.
4. Gera relatorio com presentes, ausentes, matriculados e resumo percentual.
5. Pode acessar `Perfil` e `Mapa`.

## Fluxo De Aluno

1. Entra com usuario aluno.
2. Acessa `Aluno`.
3. Consulta turmas do periodo ativo.
4. Consulta presencas registradas.
5. Envia imagens para cadastro biometrico proprio.
6. Pode acessar `Perfil` e `Mapa`.

## Mapa E IntersCity

No MVP atual, o mapa usa o snapshot local de dispositivos retornado pela API principal. A publicacao de telemetria tecnica no IntersCity fica no edge-node, usando a capability `autoponto_device_stats`.

Quando o endpoint publico de mapa for aberto, a pagina pode passar a consultar dados agregados do Collector/Discovery sob demanda, com botao de atualizar, sem websocket e sem webhook.

## Observacoes De UI

O visual foi mantido simples para facilitar retrabalho posterior. A melhoria atual prioriza organizacao, formularios funcionais e separacao de responsabilidades por pagina/componente.
