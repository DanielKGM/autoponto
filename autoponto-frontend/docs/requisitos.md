# Requisitos Do Frontend AutoPonto

Este documento descreve os requisitos implementados na interface React/Vite do MVP.

## Requisitos Funcionais

| ID | Requisito | Evidencia No Codigo |
| --- | --- | --- |
| RF-FE-01 | Permitir login com usuario e senha usando a API `/api/auth/token/`. | `features/auth/pages/SignInPage.tsx`, `shared/api.ts` |
| RF-FE-02 | Restaurar sessao com refresh token em cookie `HttpOnly`. | `carregarSessaoAutenticada` em `shared/api.ts` |
| RF-FE-03 | Exibir areas de navegacao conforme permissoes retornadas por `/api/me/`. | `app/App.tsx` |
| RF-FE-04 | Aluno deve visualizar dashboard, aulas de hoje, proximas aulas, frequencia e ultimas presencas. | `features/aluno/pages/StudentDashboardPage.tsx` |
| RF-FE-05 | Aluno, professor e admin devem consultar calendario de aulas com status de aula/aluno. | `features/calendario/pages/LessonCalendarPage.tsx` |
| RF-FE-06 | Aluno deve cadastrar, listar e revogar a propria biometria. | `features/aluno/pages/StudentBiometricsPage.tsx`, `features/aluno/studentBiometricsUtils.ts` |
| RF-FE-07 | Professor deve visualizar dashboard de chamadas abertas, pendentes, aulas do dia e presencas recentes. | `features/professor/pages/TeacherDashboardPage.tsx` |
| RF-FE-08 | Professor deve acessar detalhe de turma/aula, resumo de frequencia e eventos de reconhecimento. | `features/aulas/pages/*` |
| RF-FE-09 | Admin deve cadastrar usuarios, estrutura academica, horarios UFMA, turmas, matriculas e professores. | `features/admin/pages/AdminAcademicoPage.tsx`, `AdminResourceManager.tsx` |
| RF-FE-10 | Admin deve cadastrar nos de borda, tokens, ESP32 e consultar diagnostico IntersCity. | `features/admin/pages/AdminIotPage.tsx` |
| RF-FE-11 | A interface deve tratar erros 400, 401, 403 e 409 com mensagens compreensiveis. | `detalheErro` em `shared/api.ts` |
| RF-FE-12 | Usuario autenticado deve acessar pagina de perfil com dados, biometrias e eventos de reconhecimento. | `features/perfil/pages/ProfilePage.tsx` |
| RF-FE-13 | Mapa IoT publico e autenticado deve listar nos/dispositivos e historico do Collector. | `features/mapa/pages/PublicMapPage.tsx` |
| RF-FE-14 | Navegacao deve redirecionar login e bloquear areas conforme permissao do usuario. | `app/navigation.ts`, `app/RequireArea.tsx` |
| RF-FE-15 | A interface deve exibir graficos de telemetria com gaps reais e PIR como histograma. | `features/mapa/pages/PublicMapPage.tsx`, `shared/ui/EChart.tsx` |

## Requisitos Nao Funcionais

| ID | Requisito | Observacao |
| --- | --- | --- |
| RNF-FE-01 | O access token deve ficar apenas em memoria; refresh fica em cookie `HttpOnly`. | `shared/api.ts` |
| RNF-FE-02 | O frontend deve ser configurado por `VITE_API_URL` e `VITE_BASE_PATH`. | `vite.config.ts`, `.env.example` |
| RNF-FE-03 | O projeto deve manter estrutura simples e evolutiva: `app`, `shell`, `features`, `shared` e `scss`. | `src/` |
| RNF-FE-04 | Validacoes de biometria no cliente devem reduzir envio acidental de arquivos invalidos ou grandes. | `features/aluno/studentBiometricsUtils.ts` |
| RNF-FE-05 | O build deve funcionar no subcaminho publico `/interscity_lh/catalog/autoponto/`. | `nginx.prod.conf`, `VITE_BASE_PATH` |
| RNF-FE-06 | A interface deve permanecer funcional mesmo quando o IntersCity/Collector estiver indisponivel; apenas diagnostico e historico do mapa refletem a falha. | `PublicMapPage`, `AdminIotPage` |
| RNF-FE-07 | As telas devem ser demonstraveis sem depender de cadastro publico de usuario. | Login controlado por usuarios criados/admin |
| RNF-FE-08 | As telas devem preservar contratos tipados com o backend para aulas, biometrias, relatorios, mapa e telemetria. | `shared/types.ts` |
