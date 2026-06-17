# Requisitos Do Frontend AutoPonto

Este documento descreve os requisitos implementados na interface React/Vite do MVP.

## Requisitos Funcionais

| ID | Requisito | Evidencia No Codigo |
| --- | --- | --- |
| RF-FE-01 | Permitir login com usuario e senha usando a API `/api/auth/token/`. | `features/auth/LoginScreen.tsx`, `api.ts` |
| RF-FE-02 | Restaurar sessao com refresh token em cookie `HttpOnly`. | `carregarSessaoAutenticada` em `api.ts` |
| RF-FE-03 | Exibir areas de navegacao conforme permissoes retornadas por `/api/me/`. | `app/App.tsx` |
| RF-FE-04 | Aluno deve visualizar turmas do periodo ativo. | `features/aluno/AlunoPainel.tsx` |
| RF-FE-05 | Aluno deve visualizar suas presencas registradas. | `features/aluno/AlunoPainel.tsx` |
| RF-FE-06 | Aluno deve enviar imagens para cadastro biometrico proprio. | `features/aluno/AlunoPainel.tsx`, `shared/biometria.ts` |
| RF-FE-07 | Professor deve selecionar turma e data para gerar relatorio de presenca. | `features/professor/ProfessorPainel.tsx` |
| RF-FE-08 | Professor deve visualizar resumo de presenca da turma. | `ResumoTurma` |
| RF-FE-09 | Admin deve cadastrar usuarios, matricular alunos, vincular professores e cadastrar biometria de aluno. | `features/admin/AdminPainel.tsx` |
| RF-FE-10 | Admin deve visualizar snapshot local de dispositivos ESP32 e diagnostico dos microsservicos IntersCity. | `features/admin/AdminPainel.tsx` |
| RF-FE-11 | A interface deve tratar erros 400, 401, 403 e 409 com mensagens compreensiveis. | `detalheErro` em `api.ts` |

## Requisitos Nao Funcionais

| ID | Requisito | Observacao |
| --- | --- | --- |
| RNF-FE-01 | O access token deve ficar apenas em memoria; refresh fica em cookie `HttpOnly`. | `api.ts` |
| RNF-FE-02 | O frontend deve ser configurado por `VITE_API_URL` e `VITE_BASE_PATH`. | `vite.config.ts`, `.env.example` |
| RNF-FE-03 | O projeto deve manter estrutura simples e evolutiva: `app`, `components`, `features` e `shared`. | `src/` |
| RNF-FE-04 | Validacoes de biometria no cliente devem reduzir envio acidental de arquivos invalidos ou grandes. | `shared/biometria.ts` |
| RNF-FE-05 | O build deve funcionar no subcaminho publico `/interscity_lh/catalog/autoponto/`. | `nginx.prod.conf`, `VITE_BASE_PATH` |
| RNF-FE-06 | A interface deve permanecer funcional mesmo quando o IntersCity estiver indisponivel; apenas o diagnostico deve refletir a falha. | Admin usa snapshot local da API |
| RNF-FE-07 | As telas devem ser demonstraveis sem depender de cadastro publico de usuario. | Login controlado por usuarios criados/admin |
