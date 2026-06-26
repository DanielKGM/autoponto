import {
  AdminResourceManager,
  type AdminResourceConfig,
  type CollectionConfig,
} from "../components/AdminResourceManager";
import { PageMeta } from "../../../shared/ui/PageMeta";
import {
  formatDate,
  statusAulaClass,
  statusAulaLabel,
} from "../../../shared/domain/academicUtils";
import { formatTimeRange } from "../../../shared/domain/studentCalendarUtils";

type Collections = Record<string, Array<Record<string, any>>>;

function lookup(
  collections: Collections,
  key: string,
  id: string | null | undefined,
  label: (item: Record<string, any>) => string,
) {
  if (!id) return "-";
  const item = (collections[key] || []).find(
    (entry) => String(entry.id) === String(id),
  );
  return item ? label(item) : id;
}

function status(item: Record<string, any>) {
  return (
    <span
      className={`chip ${item.ativo || item.is_active ? "chip-green" : "chip-muted"}`}
    >
      {item.ativo || item.is_active ? "Ativo" : "Inativo"}
    </span>
  );
}

function papelLabel(value: string) {
  const labels: Record<string, string> = {
    ADMINISTRADOR: "Administrador",
    PROFESSOR: "Professor",
    ALUNO: "Aluno",
  };
  return labels[value] || value || "-";
}

const commonCollections: CollectionConfig[] = [
  { key: "usuarios-professores", endpoint: "/usuarios/?papel=PROFESSOR" },
  { key: "usuarios-alunos", endpoint: "/usuarios/?papel=ALUNO" },
];

const resources: AdminResourceConfig[] = [
  {
    key: "usuarios",
    title: "Usuários",
    singular: "usuário",
    description: "Usuários comuns, professores e administradores do sistema.",
    endpoint: "/usuarios/",
    deletable: true,
    fields: [
      { name: "username", label: "Usuário", required: true },
      {
        name: "password",
        label: "Senha",
        type: "password",
        help: "Obrigatória ao criar. Em edição, deixe vazia para manter a senha atual.",
      },
      { name: "nome_completo", label: "Nome completo" },
      { name: "email", label: "E-mail", type: "email" },
      { name: "matricula", label: "Matrícula" },
      {
        name: "papel",
        label: "Papel",
        type: "select",
        required: true,
        options: [
          { value: "ALUNO", label: "Aluno" },
          { value: "PROFESSOR", label: "Professor" },
          { value: "ADMINISTRADOR", label: "Administrador" },
        ],
      },
      { name: "is_active", label: "Ativo", type: "checkbox" },
    ],
    columns: [
      { key: "username", label: "Usuário" },
      { key: "nome_completo", label: "Nome" },
      { key: "email", label: "E-mail" },
      { key: "matricula", label: "Matrícula", align: "center" },
      {
        key: "papel",
        label: "Papel",
        align: "center",
        render: (item) => papelLabel(item.papel),
      },
      { key: "is_active", label: "Status", align: "center", render: status },
    ],
  },
  {
    key: "campi",
    title: "Campi",
    singular: "campus",
    description: "Unidades acadêmicas usadas por prédios, cursos e salas.",
    endpoint: "/campi/",
    deletable: true,
    fields: [
      { name: "nome", label: "Nome", required: true },
      { name: "ativo", label: "Ativo", type: "checkbox" },
    ],
    columns: [
      { key: "nome", label: "Nome" },
      { key: "ativo", label: "Status", align: "center", render: status },
    ],
  },
  {
    key: "predios",
    title: "Prédios",
    singular: "prédio",
    description: "Prédios vinculados a cada campus.",
    endpoint: "/predios/",
    deletable: true,
    fields: [
      {
        name: "campus",
        label: "Campus",
        type: "select",
        required: true,
        source: { key: "campi", label: (item) => item.nome },
      },
      { name: "nome", label: "Nome", required: true },
      { name: "ativo", label: "Ativo", type: "checkbox" },
    ],
    columns: [
      { key: "nome", label: "Nome" },
      {
        key: "campus",
        label: "Campus",
        render: (item, collections) =>
          lookup(collections, "campi", item.campus, (campus) => campus.nome),
      },
      { key: "ativo", label: "Status", align: "center", render: status },
    ],
  },
  {
    key: "salas",
    title: "Salas",
    singular: "sala",
    description: "Salas físicas que recebem dispositivos e aulas.",
    endpoint: "/salas/",
    deletable: true,
    fields: [
      {
        name: "predio",
        label: "Prédio",
        type: "select",
        required: true,
        source: { key: "predios", label: (item) => item.nome },
      },
      { name: "codigo", label: "Código", required: true },
      { name: "nome", label: "Nome", required: true },
      { name: "ativo", label: "Ativo", type: "checkbox" },
    ],
    columns: [
      { key: "codigo", label: "Código", align: "center" },
      { key: "nome", label: "Nome" },
      {
        key: "predio",
        label: "Prédio",
        render: (item, collections) =>
          lookup(collections, "predios", item.predio, (predio) => predio.nome),
      },
      { key: "ativo", label: "Status", align: "center", render: status },
    ],
  },
  {
    key: "periodos-letivos",
    title: "Períodos",
    singular: "período letivo",
    description: "Janelas letivas usadas para turmas e geração de aulas.",
    endpoint: "/periodos-letivos/",
    deletable: true,
    fields: [
      { name: "nome", label: "Nome", required: true },
      { name: "data_inicio", label: "Início", type: "date", required: true },
      { name: "data_fim", label: "Fim", type: "date", required: true },
      { name: "ativo", label: "Ativo", type: "checkbox" },
    ],
    columns: [
      { key: "nome", label: "Nome" },
      { key: "data_inicio", label: "Início", align: "center" },
      { key: "data_fim", label: "Fim", align: "center" },
      { key: "ativo", label: "Status", align: "center", render: status },
    ],
  },
  {
    key: "cursos",
    title: "Cursos",
    singular: "curso",
    description: "Cursos oferecidos por campus.",
    endpoint: "/cursos/",
    deletable: true,
    fields: [
      {
        name: "campus",
        label: "Campus",
        type: "select",
        required: true,
        source: { key: "campi", label: (item) => item.nome },
      },
      { name: "nome", label: "Nome", required: true },
      { name: "ativo", label: "Ativo", type: "checkbox" },
    ],
    columns: [
      { key: "nome", label: "Nome" },
      {
        key: "campus",
        label: "Campus",
        render: (item, collections) =>
          lookup(collections, "campi", item.campus, (campus) => campus.nome),
      },
      { key: "ativo", label: "Status", align: "center", render: status },
    ],
  },
  {
    key: "disciplinas",
    title: "Disciplinas",
    singular: "disciplina",
    description: "Componentes curriculares vinculados aos cursos.",
    endpoint: "/disciplinas/",
    deletable: true,
    fields: [
      {
        name: "curso",
        label: "Curso",
        type: "select",
        required: true,
        source: { key: "cursos", label: (item) => item.nome },
      },
      { name: "codigo", label: "Código", required: true },
      { name: "nome", label: "Nome", required: true },
      { name: "ativo", label: "Ativo", type: "checkbox" },
    ],
    columns: [
      { key: "codigo", label: "Código", align: "center" },
      { key: "nome", label: "Nome" },
      {
        key: "curso",
        label: "Curso",
        render: (item, collections) =>
          lookup(collections, "cursos", item.curso, (curso) => curso.nome),
      },
      { key: "ativo", label: "Status", align: "center", render: status },
    ],
  },
  {
    key: "horarios-padrao-ufma",
    title: "Horários",
    singular: "horário",
    description: "Horários normalizados da UFMA usados para gerar aulas.",
    endpoint: "/horarios-padrao-ufma/",
    deletable: true,
    fields: [
      {
        name: "codigo",
        label: "Código UFMA",
        placeholder: "2M12",
        required: true,
      },
      {
        name: "dia_semana",
        label: "Dia da semana",
        type: "number",
        required: true,
        step: "1",
      },
      { name: "horario_inicio", label: "Início", type: "time", required: true },
      { name: "horario_fim", label: "Fim", type: "time", required: true },
      { name: "ativo", label: "Ativo", type: "checkbox" },
    ],
    columns: [
      { key: "codigo", label: "Código", align: "center" },
      { key: "dia_semana", label: "Dia", align: "center" },
      { key: "horario_inicio", label: "Início", align: "center" },
      { key: "horario_fim", label: "Fim", align: "center" },
      { key: "ativo", label: "Status", align: "center", render: status },
    ],
  },
  {
    key: "turmas",
    title: "Turmas",
    singular: "turma",
    description:
      "Turmas e seus horários. Ao criar uma turma ativa, as aulas são sincronizadas.",
    endpoint: "/turmas/",
    deletable: true,
    fields: [
      {
        name: "periodo_letivo",
        label: "Período letivo",
        type: "select",
        required: true,
        source: { key: "periodos-letivos", label: (item) => item.nome },
      },
      {
        name: "disciplina",
        label: "Disciplina",
        type: "select",
        required: true,
        source: {
          key: "disciplinas",
          label: (item) => `${item.codigo} - ${item.nome}`,
        },
      },
      { name: "codigo", label: "Código", required: true },
      {
        name: "professores",
        label: "Professores",
        type: "multiselect",
        source: {
          key: "usuarios-professores",
          label: (item) => item.nome_completo || item.username,
        },
      },
      {
        name: "horarios",
        label: "Horários da turma",
        type: "schedule",
        help: "Informe sala e horário. Ao salvar, o backend cria ou ajusta as aulas dentro do período letivo.",
      },
      { name: "ativo", label: "Ativo", type: "checkbox" },
    ],
    columns: [
      { key: "codigo", label: "Código", align: "center" },
      {
        key: "disciplina",
        label: "Disciplina",
        render: (item, collections) =>
          lookup(
            collections,
            "disciplinas",
            item.disciplina,
            (disciplina) => disciplina.nome,
          ),
      },
      {
        key: "periodo_letivo",
        label: "Período",
        render: (item, collections) =>
          lookup(
            collections,
            "periodos-letivos",
            item.periodo_letivo,
            (periodo) => periodo.nome,
          ),
      },
      { key: "ativo", label: "Status", align: "center", render: status },
    ],
  },
  {
    key: "aulas",
    title: "Aulas",
    singular: "aula",
    description: "Aulas geradas a partir das turmas e horarios. Consulta paginada e somente leitura.",
    endpoint: "/aulas/",
    readOnly: true,
    fields: [],
    columns: [
      {
        key: "turma",
        label: "Turma",
        render: (item, collections) =>
          lookup(collections, "turmas", item.turma, (turma) => turma.codigo),
      },
      {
        key: "disciplina",
        label: "Disciplina",
        render: (item, collections) => {
          const turma = (collections.turmas || []).find(
            (entry) => String(entry.id) === String(item.turma),
          );
          return turma
            ? lookup(collections, "disciplinas", turma.disciplina, (disciplina) => disciplina.nome)
            : "-";
        },
      },
      {
        key: "sala",
        label: "Sala",
        align: "center",
        render: (item, collections) =>
          lookup(collections, "salas", item.sala, (sala) => sala.codigo || sala.nome),
      },
      {
        key: "data",
        label: "Data",
        align: "center",
        render: (item) => formatDate(item.data),
      },
      {
        key: "inicio",
        label: "Horario",
        align: "center",
        render: (item) => formatTimeRange(item.inicio, item.fim),
      },
      {
        key: "status",
        label: "Status",
        align: "center",
        render: (item) => (
          <span className={statusAulaClass(item.status)}>
            {statusAulaLabel(item.status)}
          </span>
        ),
      },
    ],
  },
  {
    key: "matriculas-turma",
    title: "Matrículas",
    singular: "matrícula",
    description: "Vínculo de alunos com turmas.",
    endpoint: "/matriculas-turma/",
    deletable: true,
    fields: [
      {
        name: "turma",
        label: "Turma",
        type: "select",
        required: true,
        source: { key: "turmas", label: (item) => item.codigo },
      },
      {
        name: "aluno",
        label: "Aluno",
        type: "select",
        required: true,
        source: {
          key: "usuarios-alunos",
          label: (item) => item.nome_completo || item.username,
        },
      },
      { name: "ativo", label: "Ativa", type: "checkbox" },
    ],
    columns: [
      {
        key: "turma",
        label: "Turma",
        render: (item, collections) =>
          lookup(collections, "turmas", item.turma, (turma) => turma.codigo),
      },
      {
        key: "aluno",
        label: "Aluno",
        render: (item, collections) =>
          lookup(
            collections,
            "usuarios-alunos",
            item.aluno,
            (aluno) => aluno.nome_completo || aluno.username,
          ),
      },
      { key: "ativo", label: "Status", align: "center", render: status },
    ],
  },
];

export function AdminAcademicoPage() {
  return (
    <>
      <PageMeta
        title="Admin Acadêmico | AutoPonto"
        description="Cadastro acadêmico do AutoPonto."
      />
      <AdminResourceManager
        pretitle="Admin"
        title="Acadêmico"
        description="Cadastros acadêmicos, turmas e horários com validação centralizada pela API."
        resources={resources}
        collections={commonCollections}
      />
    </>
  );
}
