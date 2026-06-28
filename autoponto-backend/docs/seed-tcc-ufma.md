# Seed UFMA/TCC

Este seed prepara um cenario demonstravel do AutoPonto para o TCC, focado no curso de Engenharia da Computacao da UFMA no campus Cidade Universitaria Dom Delgado - Sao Luis.

## O Que O Seed Cria

O comando `seed_dados_ufma` cria ou atualiza, de forma idempotente:

- Campus: Cidade Universitaria Dom Delgado - Sao Luis.
- Predios: Paulo Freire e BICT.
- Sala: 105N, nome 105 Norte, vinculada ao predio Paulo Freire.
- Periodo letivo: 2026.1, de 16/03/2026 a 18/07/2026.
- Curso: Engenharia da Computacao.
- Disciplina: EECP0021 - SISTEMAS DISTRIBUIDOS.
- Turma: 20261EECP0021.
- Professor da turma: registro de professor para a disciplina, sem expor dados pessoais neste documento.
- Alunos: registros de alunos informados para a demonstracao, sem matricula automatica na turma.
- Horarios padrao UFMA: slots de manha, tarde e noite por dia, alem dos horarios compostos 2N34 e 4N34 para a turma do TCC.
- Horarios de aula: turma 20261EECP0021 na sala 105N nos horarios 2N34 e 4N34.
- No de borda: `raspberry-tcc`, codigo `88A29E606012`, com latitude/longitude usadas no mapa publico.
- Token do no de borda: um token ativo chamado `seed-edge`, impresso no console apenas quando criado.
- ESP32: `esp32-tcc`, codigo `9084CED6CDC0`, vinculada ao no e a sala 105N, com UUID IntersCity cadastrado.

O seed nao matricula os alunos automaticamente na turma. Essa etapa fica para o painel administrativo do frontend, para demonstrar o fluxo de cadastro e vinculo durante o TCC.

Quando o token `seed-edge` ainda nao existe, o comando imprime:

```text
MAIN_API_TOKEN=<token-bruto>
```

Copie esse valor para o `MAIN_API_TOKEN` do edge-node. A API guarda apenas o hash do token; em execucoes seguintes o seed preserva o token ativo e nao consegue exibir o valor bruto novamente.

## Senhas

Por padrao, usuarios criados pelo seed ficam sem senha utilizavel. Isso evita criar senhas padrao em producao.

Para ambiente de demonstracao controlado, voce pode informar uma senha inicial:

```bash
python manage.py seed_dados_ufma --senha-padrao "troque-esta-senha"
```

## Rodar Em Desenvolvimento

Com o compose local ativo:

```bash
docker compose exec backend python /app/autoponto/manage.py seed_dados_ufma
```

Com senha inicial para demonstracao:

```bash
docker compose exec backend python /app/autoponto/manage.py seed_dados_ufma --senha-padrao "troque-esta-senha"
```

Para desenvolvimento local com uma aula valida durante o dia inteiro, todos os dias da semana, use:

```bash
docker compose exec backend python /app/autoponto/manage.py seed_dados_ufma --dev-24h
```

Esse modo cria horarios especializados `2M123456` a `8M123456`, de 00:00 a 23:59, e faz a turma do seed usar esses horarios. Ele e voltado para desenvolvimento; sem a flag, o seed volta ao horario demonstrativo normal `2N34` e `4N34`.

## Rodar Em Producao Na VM

Use o compose de producao com o `.env.prod` real da VM:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec backend python /app/autoponto/manage.py seed_dados_ufma
```

Com senha inicial temporaria para demonstracao:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec backend python /app/autoponto/manage.py seed_dados_ufma --senha-padrao "troque-esta-senha"
```

## Criar Administrador Inicial

O seed nao cria administrador. Crie manualmente:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec backend python /app/autoponto/manage.py createsuperuser
```

## Rotacionar Token Do No De Borda

O seed cria automaticamente o token inicial do no. Para rotacionar o segredo depois, autentique como administrador e emita um novo token pela API de `nos-borda`; o valor bruto tambem aparece apenas na resposta de emissao.
