import { useState } from "react";
import { apiFetch, detalheErro } from "../../api";
import {
  AdminResourceManager,
  type AdminResourceConfig,
  type CollectionConfig,
} from "../../components/admin/AdminResourceManager";
import { ConfirmModal } from "../../components/common/ConfirmModal";
import { IconButton } from "../../components/common/IconButton";
import { Modal } from "../../components/common/Modal";
import { PageMeta } from "../../components/common/PageMeta";
import { useToast } from "../../components/common/Toast";
import { CopyIcon, LockIcon } from "../../components/icons";

type TokenResponse = {
  token_id: string;
  no_id: string;
  token: string;
  prefixo_token: string;
};

type Collections = Record<string, Array<Record<string, any>>>;

function lookup(collections: Collections, key: string, id: string | null | undefined, label: (item: Record<string, any>) => string) {
  if (!id) return "-";
  const item = (collections[key] || []).find((entry) => String(entry.id) === String(id));
  return item ? label(item) : id;
}

function status(item: Record<string, any>) {
  return (
    <span className={`status ${item.ativo ? "status-green" : "status-muted"}`}>
      {item.ativo ? "Ativo" : "Inativo"}
    </span>
  );
}

function NodeTokenAction({ node }: { node: Record<string, any> }) {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState<TokenResponse | null>(null);
  const [open, setOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  async function emitToken() {
    setLoading(true);
    setToken(null);
    try {
      const response = await apiFetch<TokenResponse>(
        `/nos-borda/${node.id}/emitir-token/`,
        {
          method: "POST",
          body: JSON.stringify({ nome: "visualizacao-unica" }),
        },
      );
      setToken(response);
      setConfirmOpen(false);
      setOpen(true);
      showToast("Token gerado. Copie agora.", "success");
    } catch (error) {
      showToast(detalheErro(error), "error");
    } finally {
      setLoading(false);
    }
  }

  async function copyToken() {
    if (!token?.token) return;
    await navigator.clipboard.writeText(token.token);
    showToast("Token copiado.", "success");
  }

  return (
    <>
      <IconButton
        label="Gerar token"
        icon={<LockIcon />}
        onClick={() => setConfirmOpen(true)}
        disabled={loading}
      />
      <ConfirmModal
        open={confirmOpen}
        title="Gerar novo token"
        confirmLabel="Gerar"
        loading={loading}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={() => void emitToken()}
      >
        <p className="modal-confirm-text">
          Um novo token completo será exibido apenas uma vez. Gere somente quando estiver pronto para copiar.
        </p>
      </ConfirmModal>
      {token && (
        <Modal
          open={open}
          title="Token de visualização única"
          size="md"
          onClose={() => setOpen(false)}
          footer={
            <>
              <button type="button" className="btn btn-outline" onClick={() => setOpen(false)}>
                Fechar
              </button>
              <button type="button" className="btn btn-success" onClick={copyToken}>
                <CopyIcon />
                Copiar
              </button>
            </>
          }
        >
          <div className="token-result">
            <div className="token-result-title">Visualização única</div>
            <div className="token-prefix">
              <span>Prefixo</span>
              <code>{token.prefixo_token}</code>
            </div>
            <code>{token.token}</code>
            <p className="token-result-help">
              Copie agora. O valor completo não será exibido novamente.
            </p>
          </div>
        </Modal>
      )}
    </>
  );
}

const collections: CollectionConfig[] = [
  { key: "salas", endpoint: "/salas/" },
];

const resources: AdminResourceConfig[] = [
  {
    key: "nos-borda",
    title: "Nós de borda",
    singular: "nó de borda",
    description: "Nós que sincronizam dados locais e autenticam dispositivos de borda.",
    endpoint: "/nos-borda/",
    deletable: true,
    fields: [
      { name: "codigo", label: "Código", required: true },
      { name: "nome", label: "Nome", required: true },
      { name: "latitude", label: "Latitude", type: "number", step: "0.000001" },
      { name: "longitude", label: "Longitude", type: "number", step: "0.000001" },
      { name: "ativo", label: "Ativo", type: "checkbox" },
    ],
    columns: [
      { key: "codigo", label: "Código", align: "center" },
      { key: "nome", label: "Nome" },
      {
        key: "token_prefixo_atual",
        label: "Token",
        align: "center",
        render: (item) => item.token_prefixo_atual || "-",
      },
      { key: "latitude", label: "Latitude", align: "center" },
      { key: "longitude", label: "Longitude", align: "center" },
      { key: "ativo", label: "Status", align: "center", render: status },
    ],
    rowActions: (item) => <NodeTokenAction node={item} />,
  },
  {
    key: "dispositivos-esp32",
    title: "Dispositivos",
    singular: "dispositivo",
    description: "ESP32 cadastrados, sala de instalação e UUID IntersCity.",
    endpoint: "/dispositivos-esp32/",
    deletable: true,
    fields: [
      {
        name: "no",
        label: "Nó de borda",
        type: "select",
        source: { key: "nos-borda", label: (item) => `${item.codigo} - ${item.nome}` },
      },
      {
        name: "sala",
        label: "Sala",
        type: "select",
        source: { key: "salas", label: (item) => `${item.codigo} - ${item.nome}` },
      },
      { name: "codigo", label: "Código", required: true },
      { name: "nome", label: "Nome", required: true },
      { name: "interscity_uuid", label: "UUID IntersCity" },
      { name: "ativo", label: "Ativo", type: "checkbox" },
    ],
    columns: [
      { key: "codigo", label: "Código", align: "center" },
      { key: "nome", label: "Nome" },
      {
        key: "no",
        label: "Nó",
        render: (item, loaded) => lookup(loaded, "nos-borda", item.no, (node) => node.codigo),
      },
      {
        key: "sala",
        label: "Sala",
        render: (item, loaded) => lookup(loaded, "salas", item.sala, (sala) => sala.codigo || sala.nome),
      },
      { key: "ativo", label: "Status", align: "center", render: status },
    ],
  },
];

export function AdminIotPage() {
  return (
    <>
      <PageMeta
        title="Admin IoT | AutoPonto"
        description="Cadastro IoT do AutoPonto."
      />
      <AdminResourceManager
        pretitle="Admin"
        title="IoT"
        description="Cadastro de nós de borda, dispositivos ESP32 e geração de token exibido uma única vez."
        resources={resources}
        collections={collections}
      />
    </>
  );
}
