# Atualizacao Sugerida Para O README

Este texto pode ser incorporado ao `README.md` principal. Ele evita valores reais
de ambiente, senhas, chaves, tokens e dados pessoais.

## Papel Do Servidor Central

O servidor central do AutoPonto concentra a modelagem academica, autenticacao,
cadastro biometrico, registro consolidado de presencas, relatorios e integracao
com servicos externos. Ele tambem fornece o contrato de sincronizacao usado pelo
EdgeNode para receber o snapshot das aulas, alunos, dispositivos e embeddings
necessarios ao reconhecimento local.

## Tecnologias

- Backend: Django, Django REST Framework, SimpleJWT e PostgreSQL.
- Frontend: React, Vite, TypeScript, Sass, Leaflet e ECharts.
- Biometria: OpenCV YuNet/SFace para deteccao e embedding facial.
- Seguranca biometrica: criptografia Fernet para vetores de embedding.
- Cache: Redis para embeddings ativos, com `locmem://` apenas para testes.
- IoT e telemetria: EdgeNode, ESP32-CAM, MQTT no ambiente de borda e InterSCity para historico operacional.

## Principais Modelos Academicos

Os principais modelos do backend representam:

- `Usuario`: aluno, professor ou administrador.
- `Campus`, `Predio` e `Sala`: estrutura fisica.
- `PeriodoLetivo`, `Curso` e `Disciplina`: organizacao academica.
- `Turma` e `MatriculaTurma`: oferta da disciplina e vinculo dos alunos.
- `HorarioPadraoUFMA` e `Aula`: materializacao das aulas.
- `RegistroPresenca` e `EventoReconhecimento`: resultado da chamada e evento tecnico de reconhecimento.
- `NoBorda`, `TokenNoBorda` e `DispositivoEsp32`: infraestrutura de borda.
- `EmbeddingFacial`: embedding facial ativo, inativo ou revogado.

## Fluxo Biometrico

O aluno autenticado envia capturas do rosto pelo frontend. O backend valida
quantidade, tamanho e formato das imagens, gera o embedding com OpenCV,
compara contra embeddings ativos para evitar duplicidade, revoga embeddings
anteriores do mesmo aluno e grava o novo vetor criptografado. As capturas brutas
nao devem ser persistidas.

## Fluxo De Presenca

O EdgeNode usa o snapshot recebido do servidor central para reconhecer alunos
localmente durante a janela de uma aula. Ao reconhecer um aluno, envia um evento
para `/api/edge/attendance/`. O backend valida no, dispositivo, sala, aula,
matricula e horario antes de atualizar ou criar `RegistroPresenca` e registrar
`EventoReconhecimento`.

## Sincronizacao Com EdgeNode

O endpoint `/api/edge/pull/` entrega um snapshot do dia para o no autenticado:
dispositivos por codigo, aulas por sala, alunos por aula, alunos por id e
embeddings faciais criptografados. O EdgeNode usa esse snapshot como cache local
para operar mesmo com processamento facial fora do servidor central.

## Integracao InterSCity

O backend consulta o InterSCity Collector para historico de capacidades tecnicas
dos dispositivos. O mapa publico usa `/api/public/mapa/nos/` para exibir nos de
borda e dispositivos, e `/api/public/mapa/dispositivos/<id>/historico/` para
exibir telemetria, incluindo RSSI, heap, PSRAM, tempo de envio e histograma PIR.

## Metricas E Logs Para Testes Do TCC

Para a analise experimental, recomenda-se registrar logs estruturados para:

- tempo total de cadastro biometrico;
- tempo de geracao de embedding;
- falhas de deteccao facial;
- tempo de criptografia e descriptografia de embeddings;
- tempo de geracao do snapshot do EdgeNode;
- tempo de ingestao de presencas enviadas pelo EdgeNode;
- tempo de resposta de endpoints principais;
- falhas e latencia da integracao InterSCity.

Os logs nao devem incluir imagem, embedding em claro, token, senha, chave,
matricula real, nome real ou qualquer dado pessoal desnecessario.

## Como Rodar Localmente

Resumo do fluxo de desenvolvimento:

1. Configurar variaveis de ambiente a partir de `.env.example`, preenchendo
   valores locais sem commitar segredos.
2. Subir PostgreSQL e Redis localmente ou via Docker Compose.
3. Instalar dependencias Python no ambiente virtual.
4. Aplicar migrations e, opcionalmente, carregar dados sinteticos para testes.
5. Rodar o backend em `http://127.0.0.1:8000`.
6. Instalar dependencias do frontend.
7. Rodar o frontend em `http://127.0.0.1:5173`.

No Windows deste ambiente, o frontend costuma ser executado com
`cmd /c npm.cmd ...`.

## Limitacoes Conhecidas

- O prototipo depende de PostgreSQL local para telas com dados reais.
- A biometria depende de modelos ONNX configurados no ambiente.
- A integracao InterSCity depende de disponibilidade do Collector externo.
- O uso de `locmem://` no cache biometrico deve ficar restrito a testes.
- Capturas para relatorio devem usar dados sinteticos ou anonimizados.
- O mapa publico mostra telemetria somente para dispositivos com UUID InterSCity configurado.
