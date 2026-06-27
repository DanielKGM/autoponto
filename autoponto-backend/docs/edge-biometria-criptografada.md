# Atualizacao do EdgeNode para biometria criptografada

Este documento descreve o que o EdgeNode precisa alterar para consumir o novo contrato de biometria facial do backend AutoPonto.

Antes, o pull de sincronizacao entregava o vetor facial em claro, em `embedding.data`. Agora o backend envia apenas um ciphertext Fernet em `embedding_encrypted`. O EdgeNode deve descriptografar esse valor localmente, converter a lista para `float32` e manter o vetor descriptografado apenas no cache local em memoria/Redis.

## O que mudou no pull

Endpoint continua o mesmo:

```http
GET /api/edge/pull/?node_id=<codigo-ou-id-do-no>
```

Dentro de `cache_redis.embeddings_faciais`, cada item agora tem este formato minimo:

```json
{
  "uuid-do-embedding": {
    "alunoId": "uuid-do-aluno",
    "embedding_encrypted": "gAAAAAB..."
  }
}
```

Remover suporte obrigatorio ao formato antigo:

```json
{
  "embedding": {
    "dtype": "float32",
    "shape": [1, 128],
    "data": [0.01, 0.02]
  }
}
```

O backend nao envia mais `dtype`, `shape` nem `data`.

## Nova configuracao do EdgeNode

Adicionar a mesma chave Fernet usada no backend:

```bash
FACE_EMBEDDING_ENCRYPTION_KEY=<chave-fernet>
```

Gerar chave:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Regras:

- A chave deve ser igual no backend e no EdgeNode.
- A chave nao deve entrar no repositorio.
- Em producao, configurar por `.env`, systemd, Docker secret ou variavel de ambiente equivalente.
- Se a chave estiver ausente ou errada, o EdgeNode deve rejeitar o snapshot novo.

## Dependencia Python

Adicionar `cryptography` no ambiente do EdgeNode:

```bash
pip install cryptography
```

Se houver `requirements.txt` no EdgeNode:

```txt
cryptography
```

## Como descriptografar

Exemplo minimo:

```python
import json
import os

import numpy as np
from cryptography.fernet import Fernet


fernet = Fernet(os.environ["FACE_EMBEDDING_ENCRYPTION_KEY"].encode("ascii"))


def decrypt_embedding(ciphertext: str) -> np.ndarray:
    raw = fernet.decrypt(ciphertext.encode("ascii"))
    values = json.loads(raw.decode("utf-8"))
    return np.asarray(values, dtype=np.float32)
```

Entrada: `embedding_encrypted`.

Saida: `np.ndarray(dtype=np.float32)`.

## Atualizacao no fluxo de sync

Hoje o EdgeNode provavelmente faz algo equivalente a:

1. Chamar `/api/edge/pull/`.
2. Ler `payload["cache_redis"]`.
3. Substituir snapshot Redis local.
4. O face-worker usa `embeddings_faciais`.

Novo fluxo recomendado:

1. Baixar snapshot do backend.
2. Antes de substituir o Redis local, validar todos os `embedding_encrypted`.
3. Para cada embedding:
   - ler `alunoId`;
   - descriptografar `embedding_encrypted`;
   - converter para `float32`;
   - salvar no formato interno que o face-worker ja espera.
4. So depois de todos os embeddings descriptografarem com sucesso, substituir o snapshot local.
5. Se qualquer embedding falhar, manter o snapshot anterior e registrar erro.

Essa ordem evita derrubar reconhecimento se a chave estiver errada, se o payload vier incompleto ou se o deploy do backend/edge estiver fora de sincronia.

## Formato local sugerido no Redis do EdgeNode

O contrato externo agora e criptografado, mas o cache local do EdgeNode pode continuar guardando um formato pronto para o face-worker.

Sugestao simples:

```json
{
  "uuid-do-embedding": {
    "alunoId": "uuid-do-aluno",
    "embedding": [0.01, 0.02]
  }
}
```

Ou, se o face-worker ja usa NumPy, salvar em memoria como:

```python
{
    embedding_id: {
        "alunoId": aluno_id,
        "embedding": np.asarray(values, dtype=np.float32),
    }
}
```

O importante:

- Redis local do EdgeNode nao precisa persistir esses vetores.
- Ao reiniciar, o EdgeNode faz pull de novo e reconstrui o cache.
- Vetores descriptografados devem ficar apenas no ambiente local do EdgeNode.

## Mudancas no face-worker

O face-worker nao deve tentar ler `embedding.data` do payload do backend.

Ele deve receber o vetor ja descriptografado pelo passo de sync.

Se o codigo atual recebe isto:

```python
embedding_payload["embedding"]["data"]
```

Trocar para algum valor local ja processado, por exemplo:

```python
embedding_payload["embedding"]
```

Ou ajustar a funcao que monta o cache para entregar ao worker exatamente o formato antigo, mas preenchido depois de descriptografar:

```python
cache_local["embeddings_faciais"][embedding_id] = {
    "alunoId": aluno_id,
    "embedding": {
        "data": decrypt_embedding(ciphertext).tolist()
    },
}
```

Essa alternativa reduz mudanca no worker, mas ainda remove o vetor em claro do trafego backend -> edge.

## Tratamento de falhas

Falhas que devem impedir troca do snapshot:

- `FACE_EMBEDDING_ENCRYPTION_KEY` ausente.
- Chave Fernet invalida.
- `embedding_encrypted` ausente.
- Ciphertext invalido.
- Resultado descriptografado nao e lista numerica.

Comportamento recomendado:

1. Logar erro com `embedding_id`.
2. Nao substituir snapshot Redis local.
3. Continuar usando cache anterior, se existir.
4. Tentar novamente no proximo ciclo de sync.

## Checklist de implementacao

- Adicionar `FACE_EMBEDDING_ENCRYPTION_KEY` no ambiente do EdgeNode.
- Instalar `cryptography`.
- Alterar parser de `cache_redis.embeddings_faciais`.
- Remover leitura direta de `embedding.data` do payload remoto.
- Descriptografar `embedding_encrypted` durante o sync.
- Converter vetor para `float32`.
- So substituir cache local apos todos os embeddings serem processados.
- Manter snapshot anterior em caso de erro.
- Testar com chave correta, chave errada e payload sem embeddings.

## Testes manuais minimos

1. Subir backend com `FACE_EMBEDDING_ENCRYPTION_KEY`.
2. Cadastrar biometria de aluno.
3. Fazer pull no EdgeNode.
4. Confirmar que o payload remoto contem `embedding_encrypted`.
5. Confirmar que nao existe `embedding.data` no payload remoto.
6. Confirmar que o EdgeNode descriptografa e carrega vetor no face-worker.
7. Trocar a chave do EdgeNode para uma chave errada.
8. Confirmar que o sync falha sem apagar snapshot local anterior.
