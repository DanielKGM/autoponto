# Regras academicas e operacionais

Este documento descreve as regras de relacionamento, exclusao, atualizacao e
rotina automatizada de status das aulas no AutoPonto.

## Relacionamentos principais

- `Campus` possui `Predio`; `Predio` possui `Sala`.
- `Curso` pertence a um `Campus`; `Disciplina` pertence a um `Curso`.
- `Turma` pertence a um `PeriodoLetivo` e a uma `Disciplina`.
- `Turma.professores` vincula professores responsaveis pela turma.
- `MatriculaTurma` vincula um aluno a uma turma e deve ser preservada como historico.
- `Aula` pertence a uma `Turma`, uma `Sala` e um `HorarioPadraoUFMA`.
- `RegistroPresenca` pertence a uma `Aula` e a um aluno.
- `EventoReconhecimento` pertence a um dispositivo e pode referenciar aula, aluno candidato e embedding usado.
- `DispositivoEsp32` pode estar associado a uma `Sala` e a um `NoBorda`.
- `EmbeddingFacial` guarda o dado biometrico derivado, nunca as imagens de captura.

## Delete e update

- Registros estruturais usados por historico nao devem ser apagados fisicamente pelo fluxo administrativo.
- `Campus`, `Predio`, `Sala`, `PeriodoLetivo`, `Curso`, `Disciplina` e `HorarioPadraoUFMA` usam desativacao (`ativo=False`) no DELETE da API.
- `Turma` usa desativacao (`ativo=False`) no DELETE da API. As matriculas permanecem preservadas. Aulas futuras sem presenca e sem evento viram `CANCELADA`.
- `MatriculaTurma` usa desativacao (`ativo=False`) no DELETE da API. Frequencia historica continua calculada a partir das aulas fechadas e registros existentes.
- `Usuario` usa inativacao (`is_active=False`) no DELETE da API para preservar vinculos academicos, presencas, turmas ministradas, biometrias e eventos.
- `NoBorda` usa desativacao (`ativo=False`) no DELETE da API e tambem desativa tokens ativos.
- `DispositivoEsp32` usa desativacao (`ativo=False`) no DELETE da API.
- `RegistroPresenca` e `EventoReconhecimento` devem ser preservados como trilha historica.
- `EmbeddingFacial` revogado perde o vetor sensivel (`vetor=[]`), recebe `status=REVOGADO`, `ativo=False` e `revogado_em`.

## Geracao e cancelamento de aulas

- Turma ativa deve possuir ao menos um horario.
- Turma ativa nao pode usar periodo letivo encerrado.
- Ao criar ou editar horarios de uma turma, aulas sao geradas somente de `max(periodo.data_inicio, hoje)` ate `periodo.data_fim`.
- Edicao de horarios so altera aulas futuras sem presenca e sem evento de reconhecimento.
- Aulas futuras removidas da grade viram `CANCELADA` quando nao possuem presenca nem evento.
- Aulas fechadas, canceladas ou com historico nao devem ser alteradas automaticamente pela edicao de horarios.

## Chamada manual

- Professor responsavel ou administrador pode abrir chamada manualmente.
- Chamada manual so abre aula `PLANEJADA`.
- Abertura manual so e permitida dentro da janela da aula: `inicio <= agora <= fim`.
- Fechamento manual so fecha aula `ABERTA`.
- Fechamento manual so e permitido depois do inicio da aula.
- Aula `CANCELADA`, `FECHADA` ou fora da janela valida retorna conflito (`409`) quando a acao nao faz sentido.

## EdgeNode e abertura automatica

- O EdgeNode continua podendo abrir automaticamente uma aula `PLANEJADA` quando envia o primeiro evento valido.
- O evento precisa pertencer ao dispositivo correto, sala correta, aula correta, aluno matriculado e horario da aula.
- Essa abertura automatica continua util como fallback caso o job externo atrase ou esteja indisponivel.

## Job de status das aulas

O comando Django `atualizar_status_aulas` e idempotente e pode ser executado varias vezes sem duplicar efeitos.

Regras:

- `PLANEJADA` com `inicio <= agora < fim` vira `ABERTA`.
- `ABERTA` com `fim <= agora` vira `FECHADA`.
- `PLANEJADA` com `fim <= agora` vira `FECHADA` diretamente.
- `CANCELADA` e `FECHADA` nao mudam.

Comandos uteis:

```powershell
.venv\Scripts\python.exe autoponto-backend\autoponto\manage.py atualizar_status_aulas
.venv\Scripts\python.exe autoponto-backend\autoponto\manage.py atualizar_status_aulas --dry-run
.venv\Scripts\python.exe autoponto-backend\autoponto\manage.py atualizar_status_aulas --now 2026-06-25T08:00:00-03:00
```

Agendamento externo em Linux/cron:

```cron
*/2 * * * * cd /app && .venv/bin/python autoponto-backend/autoponto/manage.py atualizar_status_aulas
```

Recomendacao: executar a cada 1 a 5 minutos. O comando nao substitui a validacao de janela das chamadas; ele apenas mantem os status coerentes com o horario.
