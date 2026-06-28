# Guia Da API Django Para Iniciantes

Este guia explica a API do AutoPonto para quem ainda nao conhece Django/DRF. A ideia e mostrar o caminho completo: arquivo, classe, metodo, banco, autenticacao, sincronizacao com edge e resposta JSON.

## Mapa Mental

Uma request normalmente passa por este caminho:

```text
Navegador ou Raspberry
  -> URL em api/urls.py
  -> View em api/views/
  -> Serializer em api/serializers/ ou service em api/services/
  -> Selector em api/selectors/ quando a consulta precisa de status/escopo derivado
  -> Model em api/models/
  -> PostgreSQL
  -> Response JSON
```

Exemplo real:

```text
GET /api/me/
  -> urls.py aponta para MeView
  -> MeView monta usuario/permissoes
  -> Response({...})
```

## Estrutura Geral

```text
autoponto/
  manage.py
  autoponto/
    settings.py
    urls.py
  api/
    urls.py
    models/
    serializers/
    selectors/
    views/
    services/
    permissions.py
    authentication.py
    admin.py
    migrations/
```

| Grupo | Funcao |
| --- | --- |
| `models/` | Define tabelas, campos e relacoes do banco. |
| `serializers/` | Converte Model <-> JSON e valida entrada da API. |
| `selectors/` | Centraliza consultas/anotacoes reutilizaveis, como status derivado de aula. |
| `views/` | Recebe requests HTTP e devolve responses. |
| `services/` | Guarda regras de negocio que nao devem ficar espalhadas em views. |
| `permissions.py` | Decide quem pode acessar cada endpoint. |
| `authentication.py` | Implementa autenticacao especial do no de borda. |
| `urls.py` | Liga caminhos HTTP a views. |
| `admin.py` | Configura o painel administrativo do Django. |
| `migrations/` | Representa o schema do banco em arquivos versionados. |

## Settings E URLs

`autoponto/settings.py` configura Django, DRF, JWT, banco e variaveis de ambiente.

Pontos importantes:

```python
AUTH_USER_MODEL = "api.Usuario"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}
```

Isso significa:

- Por padrao, endpoints exigem login.
- Login do frontend usa JWT.
- O model de usuario padrao do Django foi substituido por `api.Usuario`.

`api/urls.py` liga endpoints a views. Existem dois estilos:

### Router

Usado para CRUD automatico com `ViewSet`.

```python
router = DefaultRouter()
router.register("cursos", CursoViewSet, basename="curso")
router.register("turmas", TurmaViewSet, basename="turma")
```

Isso cria rotas como:

```text
GET    /api/cursos/
POST   /api/cursos/
GET    /api/cursos/{id}/
PUT    /api/cursos/{id}/
DELETE /api/cursos/{id}/
```

### Path Manual

Usado para endpoints especificos.

```python
path("me/", MeView.as_view(), name="me")
path("edge/pull/", EdgePullView.as_view(), name="edge-pull")
```

## Models

Models ficam em `api/models/`. Eles definem o banco.

### Exemplo: Usuario

Arquivo: `api/models/identidade.py`

```python
class PapelUsuario(models.TextChoices):
    ALUNO = "ALUNO", "Aluno"
    PROFESSOR = "PROFESSOR", "Professor"
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"


class Usuario(AbstractUser, BaseModel):
    email = models.EmailField(blank=True, default="")
    papel = models.CharField(max_length=20, choices=PapelUsuario.choices)
    matricula = models.CharField(max_length=50, blank=True)
    nome_completo = models.CharField(max_length=255, blank=True)
```

Conceitos usados:

- `models.CharField`: coluna texto.
- `models.EmailField`: coluna de email.
- `choices`: limita valores aceitos, como `ALUNO`, `PROFESSOR`, `ADMINISTRADOR`.
- `AbstractUser`: reaproveita login/senha/permissoes do Django.
- `BaseModel`: adiciona `id`, `criado_em`, `atualizado_em`.

### Relacoes

Exemplo: uma sala pertence a um predio.

```python
class Sala(BaseModel):
    predio = models.ForeignKey(Predio, on_delete=models.CASCADE, related_name="salas")
    nome = models.CharField(max_length=255)
    codigo = models.CharField(max_length=20)
```

`ForeignKey` significa: muitos registros de `Sala` podem apontar para um `Predio`.

Exemplo: uma turma pode ter muitos professores.

```python
professores = models.ManyToManyField(Usuario, related_name="turmas_ministradas", blank=True)
```

`ManyToManyField` significa relacao muitos-para-muitos.

### Meta, Constraints E Clean

`Meta` configura ordenacao, nomes e regras de banco.

```python
class Meta:
    ordering = ("nome",)
    constraints = [
        models.UniqueConstraint(fields=("campus", "nome"), name="uq_curso_campus_nome"),
    ]
```

`clean()` guarda validacoes de negocio do model.

Exemplo em `PeriodoLetivo`:

```python
def clean(self):
    if self.data_fim < self.data_inicio:
        raise ValidationError({"data_fim": "A data final deve ser maior ou igual a data inicial."})
```

Principais models do AutoPonto:

| Model | Papel no sistema |
| --- | --- |
| `Usuario` | Admin, professor ou aluno. |
| `Campus`, `Predio`, `Sala` | Localizacao academica. |
| `PeriodoLetivo`, `Curso`, `Disciplina`, `Turma` | Estrutura minima de aulas. |
| `MatriculaTurma` | Aluno vinculado a uma turma. |
| `HorarioPadraoUFMA` | Horarios tabelados UFMA, como `2N34`. |
| `Aula` | Aula real em uma data, com turma, sala, horario UFMA e inicio/fim salvos. |
| `RegistroPresenca` | Presenca de um aluno em uma aula. |
| `NoBorda`, `TokenNoBorda`, `DispositivoEsp32` | Raspberry, token e ESP32. |
| `EmbeddingFacial` | Vetor biometrico criptografado do aluno, ativo ou revogado. |

`Aula` nao possui campo persistido `status`. O status (`PLANEJADA`, `ABERTA`, `FECHADA`, `CANCELADA`) e calculado por `api/selectors/aulas.py`:

```python
from api.selectors.aulas import status_aula, com_status_aula
```

Regras resumidas: `cancelada_em` vence tudo, `fechada_em` fecha manualmente, `fim <= agora` fecha por horario, `inicio <= agora < fim` abre a aula, e o restante fica planejado.

## Serializers

Serializers ficam em `api/serializers/`. Eles transformam models em JSON e validam JSON recebido.

### Exemplo: UsuarioSerializer

Arquivo: `api/serializers/identidade.py`

```python
class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = ("id", "username", "email", "nome_completo", "matricula", "papel", "password", "is_active")
        read_only_fields = ("id",)
```

Conceitos:

- `ModelSerializer`: cria serializer baseado em um model.
- `fields`: quais campos entram no JSON.
- `read_only_fields`: cliente nao pode enviar/alterar.
- `write_only=True`: entra na request, mas nao sai na response.

O serializer tambem personaliza senha:

```python
def create(self, validated_data):
    password = validated_data.pop("password", None)
    usuario = Usuario(**validated_data)
    if password:
        usuario.set_password(password)
    else:
        usuario.set_unusable_password()
    usuario.save()
    return usuario
```

Por que isso existe: senha nao pode ser salva como texto puro. `set_password()` cria hash seguro.

## Views

Views ficam em `api/views/`. Elas recebem HTTP e devolvem JSON.

Existem dois tipos principais aqui.

### ModelViewSet

Usado para CRUD.

Arquivo: `api/views/academico.py`

```python
class CursoViewSet(AdminReadableModelViewSet):
    queryset = Curso.objects.select_related("campus").all()
    serializer_class = CursoSerializer
    filterset_fields = ("campus", "ativo")
    search_fields = ("nome",)
```

DRF usa isso para criar:

- listar cursos;
- criar curso;
- editar curso;
- excluir curso;
- buscar por id.

Campos importantes:

- `queryset`: de onde vem os dados.
- `serializer_class`: como converter para/de JSON.
- `filterset_fields`: filtros permitidos por query string.
- `search_fields`: campos usados na busca.
- `permission_classes`: quem pode acessar.

### APIView

Usado para endpoint especifico, nao necessariamente CRUD.

Arquivo: `api/views/frontend.py`

```python
class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response({
            "usuario": _payload_usuario(request.user),
            "permissoes": _payload_permissoes(request.user),
        })
```

Exemplo de resposta:

```json
{
  "usuario": {
    "id": "uuid",
    "username": "daniel",
    "email": "",
    "nome_completo": "Daniel Campos",
    "matricula": "20250013659",
    "papel": "ALUNO"
  },
  "permissoes": {
    "areas": ["aluno"],
    "pode_administrar": false,
    "pode_emitir_relatorios": false,
    "pode_cadastrar_biometria_propria": true
  }
}
```

## Services

Services ficam em `api/services/`. Eles concentram regra de negocio.

Por que usar services: se a regra ficar dentro da view, fica dificil testar/reutilizar. A view deve lidar com HTTP; o service deve lidar com negocio.

### Exemplo: sincronizar aulas da turma

Arquivo: `api/services/aulas.py`

```python
def sincronizar_aulas_da_turma(turma: Turma, horarios: list[dict]) -> None:
    pares_desejados = _normalizar_horarios(horarios) if turma.ativo else set()
    if turma.ativo:
        _criar_ou_atualizar_aulas(turma, horarios)
    _cancelar_aulas_futuras_removidas(turma, pares_desejados)
```

Conceitos Django:

- `objects`: gerenciador padrao do model.
- `get_or_create`: usado internamente para criar a aula se ainda nao existe.
- `transaction.atomic`: garante que criacao/edicao da turma e geracao das aulas terminem juntas.

### Exemplo: consultar aulas materializadas

```python
aulas = Aula.objects.select_related("turma", "sala", "horario_padrao").filter(
    data=timezone.localdate(),
    turma__ativo=True,
)
```

Conceitos:

- `filter(...)`: gera `WHERE` no SQL.
- `campo__subcampo`: atravessa relacoes.
- `__lte`: menor ou igual.
- `__gte`: maior ou igual.
- `select_related`: otimiza consultas com `ForeignKey`.

## Permissions

Arquivo: `api/permissions.py`

Permissoes decidem quem acessa.

```python
class IsAdministrador(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.papel == PapelUsuario.ADMINISTRADOR)
```

Principais permissoes:

| Classe | Quem permite |
| --- | --- |
| `IsAdministrador` | Apenas admin. |
| `IsProfessorOuAdministrador` | Professor ou admin. |
| `IsAdministradorOuSomenteLeitura` | Admin escreve; usuarios humanos autenticados leem. |
| `IsNoBorda` | Apenas Raspberry autenticado por `NodeToken`. |

## Autenticacao Do Frontend

O frontend usa JWT.

### Login

Endpoint:

```http
POST /api/auth/token/
```

Request:

```json
{
  "username": "admin",
  "password": "senha"
}
```

Response:

```json
{
  "access": "jwt-curto"
}
```

O refresh token nao aparece no JSON. Ele fica em cookie `HttpOnly`.

Arquivo: `api/views/autenticacao.py`

```python
response = Response(dados, status=status.HTTP_200_OK)
_definir_cookie_refresh(response, refresh)
```

Por que usar cookie `HttpOnly`: JavaScript do navegador nao consegue ler esse cookie, reduzindo risco de roubo por XSS.

### Refresh

Endpoint:

```http
POST /api/auth/token/refresh/
```

O backend pega o refresh no cookie:

```python
refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
```

### Uso Do Access Token

Nas requests autenticadas:

```http
Authorization: Bearer <access-token>
```

## Autenticacao Do Edge

O Raspberry nao usa login de usuario. Ele usa `NodeToken`.

Arquivo: `api/authentication.py`

```python
class EdgeNodeTokenAuthentication(authentication.BaseAuthentication):
    keyword = "NodeToken"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8")
```

O edge envia:

```http
Authorization: NodeToken token-gerado
```

O backend:

1. Calcula hash do token bruto.
2. Busca `TokenNoBorda`.
3. Verifica se token esta ativo e nao expirou.
4. Verifica se o `NoBorda` esta ativo.
5. Atualiza `ultimo_uso_em` e `ultimo_sync_em`.
6. Retorna `request.user = no`.

Por isso endpoints edge usam:

```python
authentication_classes = (EdgeNodeTokenAuthentication,)
permission_classes = (IsNoBorda,)
```

## Sincronizacao Edge

A sincronizacao fica em `api/services/sincronizacao_borda.py` e em `api/views/edge_contract.py`.

### Teoria

O Raspberry precisa de cache local para reconhecer presencas mesmo sem consultar o backend a cada frame.

O backend envia:

- salas do no;
- ESP32 do no;
- aulas do dia;
- alunos matriculados nessas aulas;
- embeddings faciais ativos;
- um snapshot autoritativo pronto para o Redis local do edge.

### Pull

Endpoint:

```http
GET /api/edge/pull/?node_id=NO-CCET-01
Authorization: NodeToken <token>
```

Implementacao:

```python
class EdgePullView(APIView):
    authentication_classes = (EdgeNodeTokenAuthentication,)
    permission_classes = (IsNoBorda,)

    def get(self, request):
        return Response(montar_payload_pull(request.user, request.query_params))
```

O service sempre monta um snapshot do dia para o no autenticado:

```python
return {
    "snapshot_data": timezone.localdate().isoformat(),
    "synced_at": timezone.now(),
    "cache_redis": cache_pronto_para_o_edge,
}
```

Exemplo de resposta simplificada:

```json
{
  "snapshot_data": "2026-06-19",
  "synced_at": "2026-06-19T12:00:00Z",
  "cache_redis": {
    "dispositivos_por_codigo": {
      "9084CED6CDC0": {
        "dispositivo_id": "uuid-dispositivo",
        "dispositivo_codigo": "9084CED6CDC0",
        "sala_id": "uuid-sala",
        "ativo": true,
        "interscity_uuid": "8cf4ce45-3aff-4aa2-81e0-27a2fc361f09"
      }
    },
    "aulas_por_sala": {
      "uuid-sala": [
        {
          "id": "uuid-aula",
          "nome": "SISTEMAS DISTRIBUIDOS - 20261EECP0021",
          "turma_id": "uuid-turma",
          "sala_id": "uuid-sala",
          "inicio": "2026-06-19T18:30:00-03:00",
          "fim": "2026-06-19T20:10:00-03:00",
          "status": "PLANEJADA"
        }
      ]
    },
    "alunos_por_aula": {"uuid-aula": ["uuid-aluno"]},
    "alunos_por_id": {"uuid-aluno": {"nome": "DANIEL CAMPOS"}},
    "embeddings_faciais": {
      "uuid-embedding": {
        "alunoId": "uuid-aluno",
        "embedding_encrypted": "..."
      }
    }
  },
}
```

O edge nao recebe uma entidade `MatriculaAula` nem entidades completas de sincronizacao. Para descobrir os alunos de uma aula, ele usa o conjunto Redis derivado de `cache_redis.alunos_por_aula`.
Nao ha incremental, cursores nem `deleted`: quando algo deixa de ser valido para o no, o item simplesmente nao aparece no snapshot seguinte e o edge remove isso ao substituir as chaves Redis.

### Attendance

Endpoint:

```http
POST /api/edge/attendance/
Authorization: NodeToken <token>
```

Request:

```json
{
  "node_id": "88A29E606012",
  "eventos": [
    {
      "id": "evento-001",
      "aluno_id": "uuid-aluno",
      "aula_id": "uuid-aula",
      "dispositivo_id": "uuid-dispositivo",
      "reconhecido_em": "2026-06-19T18:45:00-03:00",
      "score": 0.91
    }
  ]
}
```

Validacoes principais:

```python
dispositivo = DispositivoEsp32.objects.get(id=evento["dispositivo_id"], no=no, ativo=True)
aula = Aula.objects.select_related("turma", "sala").get(id=evento["aula_id"])
aluno = Usuario.objects.get(id=evento["aluno_id"], papel=PapelUsuario.ALUNO, is_active=True)
```

Depois:

1. Dispositivo pertence ao no autenticado?
2. Aula e da mesma sala da ESP32?
3. Aluno esta matriculado na turma?
4. `reconhecido_em` esta entre `Aula.inicio` e `Aula.fim`?
5. Aula nao tem `fechada_em` nem `cancelada_em`?
6. Evento ja foi recebido antes?

Se passar:

```python
RegistroPresenca.objects.update_or_create(
    aula=aula,
    aluno=aluno,
    defaults={
        "status": RegistroPresenca.STATUS_PRESENTE,
        "registrado_em": reconhecido_em,
        "registrado_por_dispositivo": dispositivo,
    },
)
```

Response:

```json
{
  "synced_ids": ["evento-001"]
}
```

## Biometria

Fluxo:

1. Aluno ou admin envia capturas base64.
2. Serializer valida quantidade/tamanho/formato.
3. Service gera embedding com OpenCV YuNet/SFace.
4. Backend compara com embeddings ativos de outros alunos usando cache Redis; em testes pode usar `locmem://`.
5. Se nao for duplicado, revoga embeddings ativos anteriores do mesmo aluno, apaga seus vetores sensiveis e cria um novo `EmbeddingFacial` ativo.
6. O vetor fica criptografado com Fernet em repouso.
7. O pull do EdgeNode envia `embedding_encrypted`; o edge descriptografa localmente com `FACE_EMBEDDING_ENCRYPTION_KEY`.
8. Imagens nao sao persistidas.

Endpoint do aluno:

```http
POST /api/me/biometria/
```

Request:

```json
{
  "capturas": ["data:image/jpeg;base64,..."],
  "versao_modelo": "sface"
}
```

Response:

```json
{
  "embedding_id": "uuid-embedding",
  "status": "ATIVO"
}
```

Listagem e revogacao pelo aluno:

```http
GET /api/me/biometrias/
DELETE /api/me/biometrias/{embedding_id}/
```

Ao revogar, o backend define `status=REVOGADO`, `ativo=False`, `revogado_em` e limpa `vetor=[]`.

## Relatorios

Views em `api/views/frontend.py` chamam services em `api/services/relatorios.py`.

Exemplos:

```http
GET /api/relatorios/turmas/{turma_id}/presencas/?data=2026-06-19
GET /api/relatorios/turmas/{turma_id}/resumo/?inicio=2026-06-01&fim=2026-06-30
GET /api/relatorios/alunos/{aluno_id}/presencas/?turma={turma_id}
```

Regras:

- Admin ve tudo.
- Professor ve apenas turmas que ministra.
- Aluno ve apenas seus dados.

## Mapa Publico E IntersCity

O mapa publico nao exige login.

```http
GET /api/public/mapa/nos/
```

Retorna nos de borda ativos com latitude/longitude e dispositivos ESP32 ativos agrupados.

```json
[
  {
    "id": "uuid-no",
    "codigo": "88A29E606012",
    "nome": "raspberry-tcc",
    "latitude": "-2.559000",
    "longitude": "-44.309000",
    "ultimo_sync_em": "2026-06-19T12:00:00Z",
    "dispositivos": [
      {
        "id": "uuid-dispositivo",
        "codigo": "9084CED6CDC0",
        "nome": "esp32-tcc",
        "sala": "105 Norte",
        "predio": "Paulo Freire",
        "interscity_uuid": "8cf4ce45-3aff-4aa2-81e0-27a2fc361f09"
      }
    ]
  }
]
```

Historico via Data Collector:

```http
GET /api/public/mapa/dispositivos/{id}/historico/?periodo=2h
```

Periodos aceitos: `recentes`, `2h`, `1d` e `7d` via `periodo`; tambem ha fallback por `dias` limitado de 1 a 7. O backend consulta o IntersCity de forma tolerante a falhas. Se o Collector falhar, a API responde com status controlado em vez de quebrar a tela. O PIR retorna normalizado como histograma em `pir.tipo = "histograma"`.

## Principais Metodos Django/DRF Usados

| Metodo/classe | Onde aparece | Para que serve |
| --- | --- | --- |
| `models.Model` | models | Base das tabelas. |
| `ForeignKey` | models | Relacao muitos-para-um. |
| `ManyToManyField` | models | Relacao muitos-para-muitos. |
| `TextChoices` | models | Enum legivel para status/papel. |
| `Meta.constraints` | models | Regras de unicidade no banco. |
| `clean()` | models | Validacao de regra de negocio. |
| `ModelSerializer` | serializers | JSON automatico baseado em model. |
| `validate_*` | serializers | Validacao de campo. |
| `create()` / `update()` | serializers | Personaliza criacao/edicao. |
| `APIView` | views | Endpoint manual com `get`, `post`, etc. |
| `ModelViewSet` | views | CRUD completo com router. |
| `get_queryset()` | views | Filtra dados conforme usuario. |
| `perform_create()` | views | Ação antes/depois de salvar. |
| `@action` | views | Endpoint extra dentro de ViewSet. |
| `Response` | views | Retorno JSON. |
| `PermissionDenied` | views | Retorna 403. |
| `ValidationError` | serializers/services | Retorna 400. |
| `get_object_or_404` | views | Busca objeto ou retorna 404. |
| `select_related` | queries | Otimiza `ForeignKey`. |
| `prefetch_related` | queries | Otimiza `ManyToMany`. |
| `get_or_create` | services | Busca ou cria registro. |
| `update_or_create` | services | Atualiza ou cria registro. |

## Como Ler Um Endpoint Novo

Use este roteiro:

1. Abra `api/urls.py`.
2. Procure o caminho HTTP.
3. Veja qual View atende.
4. Abra a View em `api/views/`.
5. Veja `permission_classes` e `authentication_classes`.
6. Se for `ViewSet`, veja `queryset`, `serializer_class`, `filterset_fields`.
7. Abra o serializer indicado.
8. Abra os services chamados.
9. Abra os models usados pelo service.

Exemplo:

```text
/api/edge/pull/
  -> api/urls.py
  -> EdgePullView
  -> EdgeNodeTokenAuthentication + IsNoBorda
  -> montar_payload_pull
  -> DispositivoEsp32, Sala, Aula, MatriculaTurma, EmbeddingFacial
```

## Erros Comuns

| Sintoma | Causa provavel |
| --- | --- |
| `401 Unauthorized` | Access token ausente/expirado ou NodeToken invalido. |
| `403 Forbidden` | Usuario autenticado, mas papel sem permissao. |
| `400 Bad Request` | Serializer ou service recusou dados invalidos. |
| `404 Not Found` | URL errada ou objeto inexistente. |
| Edge nao recebe aulas | Nao ha aula hoje para sala do dispositivo ou horario/turma esta inativo. |
| Presenca recusada | Fora de `Aula.inicio/fim`, aluno nao matriculado, aula fechada/cancelada ou ESP32 de outro no. |

## Resumo Final

- Models definem o banco.
- Serializers validam e transformam JSON.
- Views recebem HTTP.
- Services executam regras de negocio.
- Permissions protegem por papel.
- Authentication identifica usuario humano ou no de borda.
- Edge sync envia cache do dia e recebe presencas idempotentes.
- IntersCity fica restrito ao mapa publico/telemetria IoT.
