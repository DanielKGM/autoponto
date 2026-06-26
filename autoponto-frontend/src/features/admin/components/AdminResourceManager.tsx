import {
  useEffect,
  useId,
  useMemo,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import {
  ApiError,
  apiPathFromUrl,
  apiFetch,
  detalheErro,
  type ListaApi,
  normalizarLista,
} from "../../../shared/api";
import { EditIcon, PlusIcon, RefreshIcon, TrashIcon } from "../../../shared/ui/icons";
import { ConfirmModal } from "../../../shared/ui/ConfirmModal";
import { DataTable, type DataTableColumn } from "../../../shared/ui/DataTable";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { IconButton } from "../../../shared/ui/IconButton";
import { LoadingDots } from "../../../shared/ui/LoadingDots";
import { Modal } from "../../../shared/ui/Modal";
import { useToast } from "../../../shared/ui/Toast";

type AnyRecord = Record<string, any>;

type SelectSource = {
  key: string;
  label: (item: AnyRecord) => string;
  value?: (item: AnyRecord) => string;
};

type SelectOption = {
  label: string;
  value: string;
};

export type AdminField = {
  name: string;
  label: string;
  type?:
    | "text"
    | "email"
    | "password"
    | "number"
    | "date"
    | "time"
    | "datetime-local"
    | "checkbox"
    | "select"
    | "multiselect"
    | "schedule";
  required?: boolean;
  placeholder?: string;
  help?: string;
  options?: SelectOption[];
  source?: SelectSource;
  step?: string;
};

type Collections = Record<string, AnyRecord[]>;

export type AdminColumn = DataTableColumn<AnyRecord, Collections>;

export type AdminResourceConfig = {
  key: string;
  title: string;
  singular: string;
  description: string;
  endpoint: string;
  fields: AdminField[];
  columns: AdminColumn[];
  defaults?: AnyRecord;
  deletable?: boolean | ((item: AnyRecord) => boolean);
  preparePayload?: (payload: AnyRecord, item: AnyRecord | null) => AnyRecord;
  readOnly?: boolean;
  rowActions?: (item: AnyRecord, reload: () => void) => ReactNode;
  rowActionCount?: number;
};

export type CollectionConfig = {
  key: string;
  endpoint: string;
};

type AdminResourceManagerProps = {
  title: string;
  pretitle: string;
  description: string;
  resources: AdminResourceConfig[];
  collections?: CollectionConfig[];
};

type FormMode = "create" | "edit" | null;
const MAX_COLLECTION_PAGES = 100;

function fieldInitialValue(field: AdminField, item: AnyRecord | null, defaults: AnyRecord) {
  if (field.type === "checkbox") return Boolean(item?.[field.name] ?? defaults[field.name] ?? true);
  if (field.type === "multiselect") return item?.[field.name] ?? defaults[field.name] ?? [];
  if (field.type === "schedule") return item?.[field.name] ?? defaults[field.name] ?? [];
  return item?.[field.name] ?? defaults[field.name] ?? "";
}

function initialState(resource: AdminResourceConfig, item: AnyRecord | null) {
  const defaults = resource.defaults || {};
  return Object.fromEntries(
    resource.fields.map((field) => [
      field.name,
      fieldInitialValue(field, item, defaults),
    ]),
  );
}

function formatApiError(error: unknown) {
  if (error instanceof ApiError && error.data && typeof error.data === "object") {
    const messages = Object.entries(error.data as Record<string, unknown>).flatMap(
      ([field, value]) => {
        if (Array.isArray(value)) return [`${field}: ${value.join(", ")}`];
        if (typeof value === "string") return [`${field}: ${value}`];
        if (value && typeof value === "object" && "detail" in value) {
          return [`${field}: ${String((value as { detail: unknown }).detail)}`];
        }
        return [];
      },
    );
    if (messages.length > 0) return messages.join(" ");
  }
  return detalheErro(error);
}

function optionValue(source: SelectSource, item: AnyRecord) {
  return source.value ? source.value(item) : String(item.id);
}

function coercePayload(resource: AdminResourceConfig, formState: AnyRecord, item: AnyRecord | null) {
  const payload: AnyRecord = {};
  for (const field of resource.fields) {
    const value = formState[field.name];
    if (field.type === "password" && !value) continue;
    if (field.type === "schedule") {
      const horarios = Array.isArray(value)
        ? value.filter((row) => row.sala && row.horario_padrao)
        : [];
      payload[field.name] = horarios;
      continue;
    }
    if (field.type === "checkbox") {
      payload[field.name] = Boolean(value);
      continue;
    }
    if (field.type === "number") {
      payload[field.name] = value === "" || value === null ? null : Number(value);
      continue;
    }
    if (field.type === "multiselect") {
      payload[field.name] = Array.isArray(value) ? value : [];
      continue;
    }
    payload[field.name] = value === "" ? null : value;
  }
  return resource.preparePayload ? resource.preparePayload(payload, item) : payload;
}

async function loadAllRows(endpoint: string) {
  const rows: AnyRecord[] = [];
  let path: string | null = endpoint;
  let page = 0;
  while (path && page < MAX_COLLECTION_PAGES) {
    const data: ListaApi<AnyRecord> = await apiFetch<ListaApi<AnyRecord>>(path);
    rows.push(...normalizarLista<AnyRecord>(data));
    path = Array.isArray(data) ? null : apiPathFromUrl(data.next);
    page += 1;
  }
  return rows;
}

function itemCanDelete(resource: AdminResourceConfig, item: AnyRecord) {
  if (typeof resource.deletable === "function") return resource.deletable(item);
  return Boolean(resource.deletable);
}

function actionColumnWidth(resource: AdminResourceConfig) {
  let count = resource.readOnly ? 0 : 1;
  if (resource.rowActions) count += resource.rowActionCount ?? 1;
  if (!resource.readOnly && resource.deletable) count += 1;
  return `${Math.max(72, count * 32 + 32)}px`;
}

function ScheduleField({
  value,
  onChange,
  collections,
}: {
  value: Array<{ sala?: string; horario_padrao?: string }>;
  onChange: (value: Array<{ sala?: string; horario_padrao?: string }>) => void;
  collections: Collections;
}) {
  const rows = value.length > 0 ? value : [{ sala: "", horario_padrao: "" }];
  const salas = collections.salas || [];
  const horarios = collections["horarios-padrao-ufma"] || [];

  function updateRow(index: number, key: "sala" | "horario_padrao", next: string) {
    onChange(rows.map((row, rowIndex) => (rowIndex === index ? { ...row, [key]: next } : row)));
  }

  function addRow() {
    onChange([...rows, { sala: "", horario_padrao: "" }]);
  }

  function removeRow(index: number) {
    onChange(rows.filter((_, rowIndex) => rowIndex !== index));
  }

  return (
    <div className="schedule-field">
      {rows.map((row, index) => (
        <div className="schedule-row" key={`${index}-${row.sala}-${row.horario_padrao}`}>
          <select
            className="form-control"
            value={row.sala || ""}
            onChange={(event) => updateRow(index, "sala", event.target.value)}
            aria-label="Sala do horário"
          >
            <option value="">Sala</option>
            {salas.map((sala) => (
              <option value={String(sala.id)} key={sala.id}>
                {sala.codigo ? `${sala.codigo} - ${sala.nome}` : sala.nome}
              </option>
            ))}
          </select>
          <select
            className="form-control"
            value={row.horario_padrao || ""}
            onChange={(event) => updateRow(index, "horario_padrao", event.target.value)}
            aria-label="Horário padrão"
          >
            <option value="">Horário</option>
            {horarios.map((horario) => (
              <option value={String(horario.id)} key={horario.id}>
                {horario.codigo} · {horario.horario_inicio}-{horario.horario_fim}
              </option>
            ))}
          </select>
          <IconButton
            label="Remover horário"
            icon={<TrashIcon />}
            variant="danger"
            showTooltip={false}
            onClick={() => removeRow(index)}
          />
        </div>
      ))}
      <button type="button" className="btn btn-outline btn-sm schedule-add" onClick={addRow}>
        <PlusIcon />
        Adicionar horário
      </button>
    </div>
  );
}

export function AdminResourceManager({
  title,
  pretitle,
  description,
  resources,
  collections: collectionConfigs = [],
}: AdminResourceManagerProps) {
  const formId = useId();
  const { showToast } = useToast();
  const [activeKey, setActiveKey] = useState(resources[0]?.key || "");
  const [collections, setCollections] = useState<Collections>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [search, setSearch] = useState("");
  const [formMode, setFormMode] = useState<FormMode>(null);
  const [selectedItem, setSelectedItem] = useState<AnyRecord | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<AnyRecord | null>(null);
  const activeResource = resources.find((resource) => resource.key === activeKey) || resources[0];
  const [formState, setFormState] = useState<AnyRecord>(() => initialState(activeResource, null));

  const collectionMap = useMemo(() => {
    const map = new Map<string, string>();
    resources.forEach((resource) => map.set(resource.key, resource.endpoint));
    collectionConfigs.forEach((collection) => map.set(collection.key, collection.endpoint));
    return Array.from(map.entries()).map(([key, endpoint]) => ({ key, endpoint }));
  }, [collectionConfigs, resources]);

  const collectionSignature = useMemo(
    () => collectionMap.map((collection) => `${collection.key}:${collection.endpoint}`).join("|"),
    [collectionMap],
  );

  const activeRows = collections[activeResource.key] || [];
  const tableHasActions = !activeResource.readOnly || Boolean(activeResource.rowActions);
  const tableActionsWidth = tableHasActions ? actionColumnWidth(activeResource) : undefined;

  const reload = async () => {
    setLoading(true);
    try {
      const loaded = await Promise.all(
        collectionMap.map(async (collection) => {
          const data = await loadAllRows(collection.endpoint);
          return [collection.key, data] as const;
        }),
      );
      setCollections(Object.fromEntries(loaded));
    } catch (error) {
      showToast(formatApiError(error), "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload();
  }, [collectionSignature]);

  useEffect(() => {
    setSelectedItem(null);
    setDeleteTarget(null);
    setFormMode(null);
    setFormState(initialState(activeResource, null));
    setSearch("");
  }, [activeResource.key]);

  function openCreateModal() {
    setSelectedItem(null);
    setFormState(initialState(activeResource, null));
    setFormMode("create");
  }

  function openEditModal(item: AnyRecord) {
    setSelectedItem(item);
    setFormState(initialState(activeResource, item));
    setFormMode("edit");
  }

  function closeFormModal() {
    setFormMode(null);
    setSelectedItem(null);
    setFormState(initialState(activeResource, null));
  }

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    try {
      const payload = coercePayload(activeResource, formState, selectedItem);
      const path = selectedItem
        ? `${activeResource.endpoint}${selectedItem.id}/`
        : activeResource.endpoint;
      await apiFetch(path, {
        method: selectedItem ? "PUT" : "POST",
        body: JSON.stringify(payload),
      });
      showToast(
        selectedItem
          ? `${activeResource.singular} atualizado.`
          : `${activeResource.singular} cadastrado.`,
        "success",
      );
      closeFormModal();
      await reload();
    } catch (error) {
      showToast(formatApiError(error), "error");
    } finally {
      setSaving(false);
    }
  }

  async function deleteItem() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await apiFetch(`${activeResource.endpoint}${deleteTarget.id}/`, {
        method: "DELETE",
      });
      showToast(`${activeResource.singular} excluído.`, "success");
      setDeleteTarget(null);
      await reload();
    } catch (error) {
      showToast(formatApiError(error), "error");
    } finally {
      setDeleting(false);
    }
  }

  function renderField(field: AdminField) {
    const value = formState[field.name];
    const setValue = (next: unknown) =>
      setFormState((current) => ({ ...current, [field.name]: next }));

    if (field.type === "checkbox") {
      return (
        <label className="switch admin-switch">
          <input
            type="checkbox"
            checked={Boolean(value)}
            onChange={(event) => setValue(event.target.checked)}
          />
          <span className="track" />
          <span className="switch-label">{field.label}</span>
        </label>
      );
    }

    if (field.type === "select" && field.options) {
      return (
        <select
          className="form-control"
          required={field.required}
          value={value || ""}
          onChange={(event) => setValue(event.target.value)}
        >
          <option value="">Selecione</option>
          {field.options.map((option) => (
            <option value={option.value} key={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    }

    if ((field.type === "select" || field.type === "multiselect") && field.source) {
      const options = collections[field.source.key] || [];
      return (
        <select
          className="form-control"
          required={field.required}
          multiple={field.type === "multiselect"}
          value={field.type === "multiselect" ? value || [] : value || ""}
          onChange={(event) => {
            if (field.type === "multiselect") {
              setValue(Array.from(event.currentTarget.selectedOptions).map((option) => option.value));
            } else {
              setValue(event.target.value);
            }
          }}
        >
          {field.type !== "multiselect" && <option value="">Selecione</option>}
          {options.map((option) => (
            <option value={optionValue(field.source!, option)} key={optionValue(field.source!, option)}>
              {field.source!.label(option)}
            </option>
          ))}
        </select>
      );
    }

    if (field.type === "schedule") {
      return (
        <ScheduleField
          value={Array.isArray(value) ? value : []}
          onChange={setValue}
          collections={collections}
        />
      );
    }

    return (
      <input
        className="form-control"
        type={field.type || "text"}
        value={value ?? ""}
        required={field.required}
        placeholder={field.placeholder}
        step={field.step}
        onChange={(event) => setValue(event.target.value)}
      />
    );
  }

  const formTitle =
    formMode === "edit"
      ? `Editar ${activeResource.singular}`
      : `Novo ${activeResource.singular}`;

  return (
    <>
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <div className="page-pretitle">{pretitle}</div>
            <h1 className="page-title">{title}</h1>
            <p className="page-description">{description}</p>
          </div>
        </div>
      </div>

      <div className="admin-resource-tabs" aria-label="Seções administrativas">
        {resources.map((resource) => (
          <button
            type="button"
            key={resource.key}
            className={`chart-tab ${resource.key === activeResource.key ? "active" : ""}`}
            onClick={() => setActiveKey(resource.key)}
          >
            {resource.title}
          </button>
        ))}
      </div>

      <section className="card admin-table-card">
        <div className="card-header">
          <div>
            <div className="card-title">{activeResource.title}</div>
            <div className="card-subtitle">{activeResource.description}</div>
          </div>
          <div className="page-actions">
            <input
              className="form-control admin-search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar"
              aria-label="Buscar registros"
            />
            <IconButton
              label="Atualizar"
              icon={<RefreshIcon />}
              onClick={() => void reload()}
            />
            {!activeResource.readOnly && (
              <IconButton
                label={`Novo ${activeResource.singular}`}
                icon={<PlusIcon />}
                variant="primary"
                onClick={openCreateModal}
              />
            )}
          </div>
        </div>
        <div className="card-body p-0">
          {loading ? (
            <div className="admin-loading">
              <LoadingDots label="Carregando registros" />
            </div>
          ) : (
            <DataTable
              className="admin-table"
              columns={activeResource.columns}
              context={collections}
              emptyState={
                <EmptyState
                  title="Nenhum registro"
                  text="Use o botão de adicionar para criar o primeiro item desta seção."
                />
              }
              rowActions={tableHasActions ? (row) => (
                <>
                  {!activeResource.readOnly && (
                    <IconButton
                      label="Editar"
                      icon={<EditIcon />}
                      onClick={() => openEditModal(row)}
                    />
                  )}
                  {activeResource.rowActions?.(row, reload)}
                  {!activeResource.readOnly && itemCanDelete(activeResource, row) && (
                    <IconButton
                      label="Excluir"
                      icon={<TrashIcon />}
                      variant="danger"
                      onClick={() => setDeleteTarget(row)}
                    />
                  )}
                </>
              ) : undefined}
              actionsWidth={tableActionsWidth}
              rows={activeRows}
              search={search}
            />
          )}
        </div>
      </section>

      <Modal
        open={formMode !== null}
        title={formTitle}
        size="lg"
        onClose={closeFormModal}
        footer={
          <>
            <button type="button" className="btn btn-outline" onClick={closeFormModal}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary" form={formId} disabled={saving}>
              {saving ? "Salvando..." : "Salvar"}
            </button>
          </>
        }
      >
        <form className="modal-form admin-form" id={formId} onSubmit={submitForm}>
          <p className="modal-form-intro">
            Campos com regras de negócio são validados pela API.
          </p>
          {activeResource.fields.map((field) => (
            <div
              className={`modal-form-row ${field.type === "schedule" ? "form-group-wide" : ""}`}
              key={field.name}
            >
              {field.type !== "checkbox" && (
                <label className="form-label">{field.label}</label>
              )}
              {renderField(field)}
              {field.help && <div className="form-help">{field.help}</div>}
            </div>
          ))}
        </form>
      </Modal>

      <ConfirmModal
        open={deleteTarget !== null}
        title={`Excluir ${activeResource.singular}`}
        confirmLabel="Excluir"
        variant="danger"
        loading={deleting}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={() => void deleteItem()}
      >
        <p className="modal-confirm-text">
          Esta ação remove o registro selecionado. Se ele estiver protegido por outros dados,
          a API recusará a exclusão.
        </p>
      </ConfirmModal>
    </>
  );
}
