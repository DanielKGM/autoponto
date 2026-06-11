# Explicacao Geral Do Backend

Este backend e uma API Django/DRF para frequencia academica automatizada por IoT. O AutoPonto guarda o dominio academico minimo para presenca, biometria, relatorios e sincronizacao com Raspberry/ESP32. Ele nao tenta ser um sistema academico completo.

## Organizacao Do Codigo

- `autoponto/api/models/`: define as tabelas e regras basicas de integridade.
- `autoponto/api/serializers/`: valida entrada e transforma modelos em JSON.
- `autoponto/api/views/`: concentra endpoints HTTP para frontend, admin, edge e Interscity.
- `autoponto/api/services/`: guarda regras de negocio reutilizaveis, como gerar aula, fechar chamada, registrar presenca e sincronizar edge.
- `autoponto/api/tests/`: cobre contratos principais do MVP.
- `autoponto/data/models/`: local esperado para os modelos ONNX de biometria; a pasta fica versionada com `.gitkeep`, mas os `.onnx` nao entram no Git.

Todos os modelos de dominio herdam de `BaseModel`, que adiciona:

- `id`: UUID publico usado nas APIs e no edge.
- `criado_em`: data de criacao do registro.
- `atualizado_em`: data da ultima alteracao, usada tambem por sincronizacao incremental.

## Modelos E Campos

### Usuario

Representa aluno, professor ou administrador.

- `username`: identificador de login.
- `email`: contato e identificador unico auxiliar.
- `papel`: define permissao principal: `ALUNO`, `PROFESSOR` ou `ADMINISTRADOR`.
- `matricula`: codigo institucional do aluno; fica vazio para professores/admins se nao for necessario.
- `nome_completo`: nome exibido em telas e relatorios.
- Campos herdados do Django, como `password`, `is_active`, `is_staff` e `is_superuser`, continuam existindo para autenticacao e admin.

### Campus, Predio E Sala

Modelam apenas a localizacao necessaria para colocar ESP32 em salas.

- `Campus.nome`: nome do campus, por exemplo `Campus Dom Delgado`.
- `Campus.codigo`: codigo curto para integracao e administracao.
- `Campus.ativo`: permite ocultar campus sem apagar historico.
- `Predio.campus`: campus ao qual o predio pertence.
- `Predio.nome`: nome do predio ou centro.
- `Predio.codigo`: codigo curto unico dentro do campus.
- `Predio.ativo`: indica se ainda participa do MVP.
- `Sala.predio`: predio onde a sala fica.
- `Sala.nome`: nome legivel da sala.
- `Sala.codigo`: codigo curto unico dentro do predio.
- `Sala.ativo`: se falso, a sala deixa de ser enviada ao edge.

### PeriodoLetivo, Curso, Disciplina E Turma

Guardam o minimo academico para saber quem deveria estar presente.

- `PeriodoLetivo.nome`: identificador como `2026.1`.
- `PeriodoLetivo.data_inicio` e `data_fim`: delimitam quando as turmas geram aulas.
- `PeriodoLetivo.ativo`: marca o semestre atualmente usado em telas de aluno.
- `Curso.campus`: campus onde o curso e ofertado.
- `Curso.codigo`: codigo curto do curso.
- `Curso.nome`: nome do curso.
- `Curso.ativo`: permite manter historico sem listar curso encerrado.
- `Disciplina.curso`: curso ao qual a disciplina pertence.
- `Disciplina.codigo`: codigo institucional da disciplina.
- `Disciplina.nome`: nome exibido nos relatorios.
- `Disciplina.ativo`: controla se novas aulas da disciplina entram na sincronizacao.
- `Turma.periodo_letivo`: periodo em que a turma acontece.
- `Turma.disciplina`: disciplina ministrada.
- `Turma.codigo`: identificador da turma, como `A` ou `01`.
- `Turma.professores`: professores autorizados a ver relatorios e fechar chamada.
- `Turma.ativo`: se falso, a turma deixa de gerar contexto para o edge.

### MatriculaTurma

Liga aluno e turma.

- `turma`: turma em que o aluno esta matriculado.
- `aluno`: usuario com papel `ALUNO`.
- `ativo`: se falso, o aluno deixa de aparecer como matriculado nas proximas sincronizacoes.

Ausencias nao sao gravadas como linhas. O relatorio considera ausente quando nao existe `RegistroPresenca` para o aluno naquela aula.

### HorarioAula

Define a regra semanal de geracao de aulas.

- `turma`: turma daquele horario.
- `sala`: sala onde a aula acontece; e por ela que o edge associa ESP32 ao contexto.
- `dia_semana`: inteiro de 0 a 6, seguindo Python: segunda `0`, domingo `6`.
- `horario_inicio` e `horario_fim`: duracao da aula.
- `abre_chamada_minutos`: quantos minutos depois do inicio da aula a presenca comeca a valer.
- `fecha_chamada_minutos`: quantos minutos depois do inicio a presenca para de valer; se vazio, vale ate o fim da aula.
- `ativo`: desativa a regra sem apagar aulas ja materializadas.

Quando a janela muda, o backend recalcula somente aulas futuras ainda nao fechadas/canceladas.

### Aula

E a ocorrencia real de um `HorarioAula` em uma data.

- `horario`: regra semanal que originou a aula.
- `data`: dia da aula.
- `inicio` e `fim`: duracao real da aula naquele dia.
- `chamada_inicio` e `chamada_fim`: snapshot da janela de presenca usada naquele dia.
- `status`: `PLANEJADA`, `ABERTA`, `FECHADA` ou `CANCELADA`.
- `fechada_em`: quando professor/admin fechou manualmente a chamada.
- `fechada_por`: usuario que fechou a chamada.

O snapshot em `Aula` existe para que relatorios antigos continuem explicaveis mesmo que o horario da turma mude depois.

### RegistroPresenca

Representa a presenca consolidada de um aluno em uma aula.

- `aula`: aula onde a presenca foi registrada.
- `aluno`: aluno reconhecido ou marcado.
- `status`: `PRESENTE`, `AUSENTE`, `ATRASO` ou `JUSTIFICADA`.
- `registrado_em`: instante do reconhecimento ou registro manual.
- `registrado_por_dispositivo`: ESP32 que originou a presenca, quando veio do edge.

Ha restricao de uma presenca por aluno/aula.

### EventoReconhecimento

Guarda auditoria tecnica do reconhecimento enviado pelo edge.

- `id_evento_origem`: identificador gerado no edge para idempotencia.
- `dispositivo`: ESP32 que capturou o evento.
- `aula`: aula associada ao contexto.
- `aluno_candidato`: aluno reconhecido.
- `confianca`: score do reconhecimento.
- `reconhecido`: indica se o evento virou presenca.
- `ocorrido_em`: quando o reconhecimento aconteceu.

O modelo nao salva frame, imagem, embedding ou payload bruto.

### NoBorda, TokenNoBorda E DispositivoEsp32

Modelam a camada IoT.

- `NoBorda.codigo`: identificador do Raspberry em requests `node_id`.
- `NoBorda.nome`: nome legivel do no.
- `NoBorda.ativo`: controla se o no pode sincronizar.
- `NoBorda.ultimo_sync_em`: ultima sincronizacao conhecida.
- `NoBorda.interscity_uuid`: UUID do recurso equivalente no Interscity, se existir.
- `TokenNoBorda.no`: no dono do token.
- `TokenNoBorda.nome`: nome administrativo do token.
- `TokenNoBorda.prefixo_token`: trecho visivel para identificar o token sem expor o segredo.
- `TokenNoBorda.hash_token`: hash do token real.
- `TokenNoBorda.ativo`, `expira_em`, `ultimo_uso_em`: controle de uso do token.
- `DispositivoEsp32.no`: Raspberry responsavel pela ESP32.
- `DispositivoEsp32.sala`: sala monitorada.
- `DispositivoEsp32.codigo`: identificador unico da ESP32.
- `DispositivoEsp32.nome`: nome legivel.
- `DispositivoEsp32.ativo`: controla envio ao edge.
- `DispositivoEsp32.ultimo_sync_em`: reservado para telemetria de sincronizacao.
- `DispositivoEsp32.interscity_uuid`: UUID do recurso ESP32 no Interscity.

Somente o Raspberry autentica no backend principal. A ESP32 fica subordinada ao no.

### ComandoBorda

Fila comandos para Raspberry/ESP32.

- `no`: Raspberry que deve receber o comando.
- `dispositivo`: ESP32 de destino, opcional quando o comando e para o proprio no.
- `tipo`: tipo de acao, por exemplo `display_message`.
- `payload`: dados necessarios para executar o comando.
- `status`: `PENDENTE`, `ENTREGUE`, `FALHOU` ou `REJEITADO`.
- `origem`: `backend` ou `interscity`.
- `id_origem`: identificador externo para idempotencia quando vem do Interscity.
- `capacidade`: capability Interscity relacionada, como `autoponto_edge_command`.
- `criado_por`: usuario admin que criou o comando no backend; fica vazio para comandos vindos do Interscity.
- `entregue_em`: quando o edge confirmou entrega.
- `ultimo_erro`: mensagem enviada pelo edge em caso de falha.

### PerfilBiometrico E EmbeddingFacial

Guardam somente o necessario para reconhecimento.

- `PerfilBiometrico.aluno`: aluno dono da biometria.
- `PerfilBiometrico.status`: `PENDENTE`, `ATIVO` ou `INATIVO`.
- `EmbeddingFacial.perfil`: perfil dono do vetor.
- `EmbeddingFacial.versao_modelo`: modelo usado, como `sface`.
- `EmbeddingFacial.vetor`: embedding facial enviado ao edge.
- `EmbeddingFacial.status`: `ATIVO`, `INATIVO` ou `REVOGADO`.
- `EmbeddingFacial.ativo`: facilita garantir apenas um embedding ativo por aluno.

O backend compara o novo vetor com embeddings ativos de outros alunos e bloqueia duplicidade pelo limite `FACE_DUPLICATE_THRESHOLD`.

Os embeddings sao gerados com OpenCV YuNet/SFace. O backend usa os mesmos arquivos indicados no `referencia-edge/README.md`:

- `data/models/face_detection_yunet.onnx`: detector YuNet.
- `data/models/face_recognition_sface.onnx`: reconhecedor SFace.

Esses caminhos sao configurados por `FACE_DETECT_MODEL_PATH` e `FACE_RECOG_MODEL_PATH`. Se forem relativos, o backend resolve a partir de `autoponto-backend/autoponto/`. Se algum arquivo estiver ausente, o cadastro biometrico retorna erro de dominio em portugues e nao tenta persistir imagem.

## Fluxos Principais

### Frontend

- Aluno usa `/api/me/`, `/api/me/turmas/`, `/api/me/presencas/` e `/api/me/biometria/`.
- Professor usa `/api/professor/turmas/`, relatorios e `POST /api/aulas/{id}/fechar-chamada/`.
- Administrador usa CRUDs, vinculos, biometria de aluno, comandos de borda e diagnostico Interscity.

### Edge

O Raspberry autentica com `Authorization: NodeToken <token>` e usa:

- `GET /api/edge/pull`: baixa salas, dispositivos, aulas, alunos, matriculas e embeddings.
- `POST /api/edge/attendance`: envia eventos reconhecidos.
- `GET /api/edge/commands`: busca comandos pendentes.
- `POST /api/edge/commands/ack`: confirma resultado.

O contrato externo usa nomes em ingles por compatibilidade com o `referencia-edge`, mas o dominio interno fica em portugues.

### Interscity

O cliente `ClienteInterSCity` usa `INTERSCITY_BASE_URL` e paths de microsservicos. Toda chamada tem timeout e retorno controlado, entao falha externa nao bloqueia login, CRUD, biometria, presencas, relatorios ou edge sync.

## Testes

- `test_models.py`: regras de dominio, unicidade e janela de chamada.
- `test_api.py`: login, schema e fluxo administrativo basico.
- `test_biometria.py`: geracao de embedding mockada, descarte de imagens e validacao de caminho dos modelos ONNX.
- `test_edge_integracao.py`: pull, presenca, idempotencia, isolamento por no e comandos.
- `test_frontend_api.py`: endpoints por papel, relatorios, fechamento de chamada e comando administrativo.
- `test_interscity.py`: cliente HTTP e diagnostico dos cinco microsservicos.
