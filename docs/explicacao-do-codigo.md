# Explicacao Geral Do Codigo

Este backend e uma API Django/DRF para automatizacao de frequencia academica. A ideia central e manter o AutoPonto como sistema academico canonico e usar edge/Interscity apenas para a camada IoT.

## Modelos

Os modelos ficam em `autoponto/api/models/`.

- `identidade.py`: define `Usuario` e `PapelUsuario`. Um usuario pode ser aluno, professor ou administrador.
- `academico.py`: define `Campus`, `Predio`, `Sala`, `PeriodoLetivo`, `Curso`, `Disciplina`, `Turma`, `MatriculaTurma` e `HorarioAula`.
- `presencas.py`: define `Aula`, `RegistroPresenca` e `EventoReconhecimento`. `Aula` e a ocorrencia real de um `HorarioAula` em uma data.
- `dispositivos.py`: define `NoBorda`, `TokenNoBorda`, `DispositivoEsp32` e `ComandoBorda`. A ESP32 nao autentica diretamente no backend; ela fica vinculada ao no Raspberry.
- `biometria.py`: define `PerfilBiometrico` e `EmbeddingFacial`. Imagens de cadastro nao sao persistidas.

Todos herdam de `BaseModel`, que fornece UUID, `criado_em` e `atualizado_em`.

## Servicos

Os servicos ficam em `autoponto/api/services/` e concentram regras de negocio fora das views.

- `aulas.py`: cria ou lista aulas a partir dos horarios cadastrados.
- `presencas.py`: registra presenca e evento de reconhecimento.
- `biometria.py`: gera embedding com OpenCV YuNet/SFace e grava somente o vetor.
- `sincronizacao_borda.py`: adapta o dominio em portugues para o contrato em ingles usado pelo Raspberry.
- `interscity.py`: encapsula chamadas HTTP para Catalog, Adaptor, Collector, Discovery e Actuator.

## Endpoints Administrativos

Os endpoints administrativos ficam em portugues:

- `/api/usuarios/`
- `/api/campi/`, `/api/predios/`, `/api/salas/`
- `/api/periodos-letivos/`, `/api/cursos/`, `/api/disciplinas/`, `/api/turmas/`
- `/api/matriculas-turma/`, `/api/horarios-aula/`
- `/api/nos-borda/`, `/api/dispositivos-esp32/`
- `/api/aulas/`, `/api/presencas/`
- `/api/perfis-biometricos/`, `/api/embeddings-faciais/`

Administradores podem cadastrar e alterar dados. Professores podem consultar aulas e presencas relevantes.

## Edge

O Raspberry usa `NodeToken` e acessa:

- `GET /api/edge/pull`
- `POST /api/edge/attendance`
- `GET /api/edge/commands`
- `POST /api/edge/commands/ack`

Esses endpoints mantem nomes externos como `lessons`, `students` e `face_embeddings` porque o edge de referencia ja espera esse formato. Internamente, esses dados correspondem a `Aula`, `Usuario` e `EmbeddingFacial`.

## Biometria

O endpoint `/api/perfis-biometricos/matricular/` recebe capturas base64, chama `GeradorEmbeddingVisao`, grava um `EmbeddingFacial` ativo e inativa o embedding anterior do aluno. O backend nao salva frames, imagens ou payloads brutos.

## Interscity

O Interscity representa recursos IoT e capacidades. O AutoPonto usa `interscity_uuid` em `DispositivoEsp32` e `NoBorda` para relacionar recursos externos com entidades internas.

O webhook `/api/interscity/webhooks/actuator/` recebe comandos do Interscity e cria `ComandoBorda` pendente. O Raspberry busca e confirma esses comandos pelos endpoints edge.

## Testes

Os testes ficam em `autoponto/api/tests/`.

- `test_models.py`: valida regras de dominio, unicidade e biometria.
- `test_api.py`: valida autenticacao JWT, schema e endpoints administrativos.
- `test_biometria.py`: valida geracao de embedding com OpenCV mockado e descarte de frames.
- `test_edge_integracao.py`: valida pull, envio de presenca, isolamento por no e comandos.
- `test_interscity.py`: valida o cliente HTTP Interscity com chamadas mockadas.

## Seed UFMA

O comando `python manage.py seed_dados_ufma` cria um exemplo de Campus Dom Delgado, CCET, uma sala, o curso de Engenharia da Computacao e algumas disciplinas. Ele e apenas uma fixture de demonstracao; a modelagem continua generica para outros cursos/campi.
