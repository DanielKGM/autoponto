# Paginas E Fluxos Do Frontend

Este documento descreve a estrutura atual do frontend React/Vite e os fluxos demonstraveis no MVP do TCC.

## Estrutura

- `src/app/App.tsx`: rotas publicas, rotas privadas e redirecionamentos.
- `src/app/navigation.ts`: areas, rotulos, menus por permissao e destino apos login.
- `src/shell/`: layout autenticado, sidebar, header e menu do usuario.
- `src/features/auth/pages/SignInPage.tsx`: login com JWT e refresh via cookie HttpOnly.
- `src/features/aluno/pages/StudentDashboardPage.tsx`: resumo do aluno, aulas de hoje, proximas aulas e frequencia.
- `src/features/aluno/pages/StudentBiometricsPage.tsx`: cadastro, listagem e revogacao de biometria propria.
- `src/features/calendario/pages/LessonCalendarPage.tsx`: calendario de aulas para aluno, professor e admin.
- `src/features/aulas/pages/*`: detalhes de turma/aula e chamada.
- `src/features/professor/pages/TeacherDashboardPage.tsx`: dashboard do professor, chamadas e turmas.
- `src/features/admin/pages/AdminAcademicoPage.tsx`: usuarios, estrutura academica, horarios UFMA, turmas e vinculos.
- `src/features/admin/pages/AdminIotPage.tsx`: nos de borda, tokens, ESP32 e diagnostico IntersCity.
- `src/features/mapa/pages/PublicMapPage.tsx`: mapa publico e mapa embutido autenticado.
- `src/features/perfil/pages/ProfilePage.tsx`: dados da conta, biometrias e eventos de reconhecimento.
- `src/shared`: API, sessao, tipos, UI, dominio, tema e assets.

O arquivo antigo `src/App.tsx` foi removido. O ponto de entrada `src/main.tsx` importa diretamente `src/app/App.tsx`.

## Fluxo De Administrador

1. Entra com usuario administrador.
2. Vai para `/app/admin/academico`.
3. Cadastra usuarios, campus, predios, salas, periodos, cursos, disciplinas e horarios UFMA.
4. Cadastra ou edita turmas com pares de `sala` + `horario_padrao`; o backend materializa as aulas futuras.
5. Matricula alunos em turmas e vincula professores responsaveis.
6. Em `/app/admin/iot`, cadastra nos de borda, emite tokens e cadastra ESP32 com sala e UUID IntersCity.
7. Consulta calendario, detalhes de turma/aula e relatorios com permissao administrativa.
8. Pode acessar `Mapa IoT` e `Perfil`.

## Fluxo De Professor

1. Entra com usuario professor.
2. Vai para `/app/professor`.
3. Ve chamadas abertas, chamadas pendentes, aulas do dia e presencas recentes.
4. Acessa o calendario em `/app/calendario`.
5. Entra no detalhe de turma/aula por `/app/turmas/:turmaId` ou `/app/aulas/:aulaId`.
6. Acompanha presentes, ausentes, pendentes, eventos de reconhecimento e resumo de frequencia.
7. Pode acessar `Perfil` e `Mapa IoT`.

## Fluxo De Aluno

1. Entra com usuario aluno.
2. Vai para `/app/aluno`.
3. Ve aulas de hoje, proximas aulas, frequencia por turma e ultimas presencas.
4. Acessa o calendario em `/app/calendario` e detalhes de aula/turma.
5. Envia imagens para cadastro biometrico proprio em `/app/aluno/biometria`.
6. Lista biometrias ativas/revogadas e pode revogar a propria biometria.
7. Pode acessar `Perfil` e `Mapa IoT`.

## Mapa E IntersCity

O mapa publico fica em `/mapa-iot` e tambem aparece autenticado em `/app/mapa-iot`.

- `GET /api/public/mapa/nos/`: lista nos de borda ativos com coordenadas e seus dispositivos ativos.
- `GET /api/public/mapa/dispositivos/{id}/historico/?periodo=2h|1d|7d|recentes`: consulta historico do Data Collector via backend.

As coordenadas pertencem ao `NoBorda`, e cada dispositivo ESP32 carrega sala, predio e `interscity_uuid`. A publicacao de telemetria tecnica no IntersCity fica no edge-node. A API principal apenas le o Collector para montar historico, ultimo valor e histograma PIR.

## Observacoes De UI

O visual atual e uma ferramenta operacional: sidebar, header, tabelas densas, formularios, modais, cards de status e graficos. A melhoria prioriza organizacao, fluxos demonstraveis e separacao de responsabilidades por pagina/componente.
