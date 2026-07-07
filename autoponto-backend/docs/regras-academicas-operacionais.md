# Regras academicas e operacionais

Este documento descreve as regras de relacionamento, exclusao, atualizacao e
status derivado das aulas no AutoPonto.

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

- Professor responsavel ou administrador pode acessar a chamada manualmente.
- O backend nao persiste um campo `status` em `Aula`; a abertura e derivada da janela da aula.
- A chamada so fica aberta durante a janela `inicio <= agora < fim`, quando `status_aula(aula)` retorna `ABERTA`.
- Fechamento manual so fecha aula `ABERTA`.
- Fechamento manual so e permitido depois do inicio da aula.
- Fechamento manual preenche `fechada_em` e `fechada_por`; ele nao altera `fim`.
- Aula cancelada, fechada ou fora da janela valida retorna conflito (`409`) quando a acao nao faz sentido.

## EdgeNode e presenca automatica

- O EdgeNode registra presenca quando envia um evento valido dentro da janela da aula.
- O evento precisa pertencer ao dispositivo correto, sala correta, aula correta, aluno matriculado e horario da aula.
- Como o status e derivado, nao ha transicao persistida de `PLANEJADA` para `ABERTA`; a aula aparece aberta enquanto `inicio <= agora < fim`.

## Status derivado das aulas

O status exibido pela API e calculado em `api/selectors/aulas.py`, por `status_aula`, `com_status_aula` e `filtrar_status_aula`. Nao existe comando `atualizar_status_aulas` nem agendamento externo para mudar status por cron.

Regras:

- `cancelada_em` preenchido retorna `CANCELADA`.
- `fechada_em` preenchido retorna `FECHADA`.
- `fim <= agora` retorna `FECHADA`.
- `inicio <= agora < fim` retorna `ABERTA`.
- Caso contrario, retorna `PLANEJADA`.

Endpoints que listam aulas usam anotacao SQL com esse status derivado. Services que precisam decidir regra de negocio chamam `status_aula(aula, agora=None)`. Isso evita migracao e evita divergencia entre banco, calendario, relatorios e edge sync.
