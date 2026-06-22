import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router";
import L from "leaflet";
import "leaflet.markercluster";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { apiFetch, carregarSessaoAutenticada, detalheErro } from "../api";
import { BrandLogo } from "../components/common/BrandLogo";
import { PageMeta } from "../components/common/PageMeta";
import { ThemeToggleButton } from "../components/common/ThemeToggleButton";
import { Button } from "../components/ui/Button";
import type {
  DispositivoHistorico,
  DispositivoStatus,
  NoBordaMapa,
} from "../types";

type PublicMapPageProps = {
  embedded?: boolean;
};

type NodeWithCoords = NoBordaMapa & {
  lat: number;
  lng: number;
};

const UFMA_CENTER: [number, number] = [-2.5583, -44.3077];
const METRICS = [
  ["heap_free", "Heap livre"],
  ["heap_min", "Heap minimo"],
  ["heap_max", "Maior heap"],
  ["psram_free", "PSRAM livre"],
  ["psram_min", "PSRAM minima"],
  ["psram_max", "Maior PSRAM"],
  ["rssi", "RSSI"],
  ["post_max_ms", "POST maximo"],
] as const;

function parseNodes(nodes: NoBordaMapa[]): NodeWithCoords[] {
  return nodes.flatMap((node) => {
    const lat = Number(node.latitude);
    const lng = Number(node.longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return [];
    return [{ ...node, lat, lng }];
  });
}

function escapeHtml(value: string | null | undefined): string {
  return (value || "-").replace(/[&<>"']/g, (char) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return entities[char];
  });
}

function formatDate(value: string | null | undefined) {
  if (!value) return "Sem sincronizacao registrada";
  return new Date(value).toLocaleString("pt-BR");
}

function formatMetric(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "number") return value.toLocaleString("pt-BR");
  if (typeof value === "string") return value;
  if (typeof value === "boolean") return value ? "Sim" : "Nao";
  return JSON.stringify(value);
}

function metricValue(history: DispositivoHistorico | null, key: string) {
  const latest = history?.ultimo?.[key];
  if (!latest) return "-";
  return formatMetric(latest.value ?? latest.valor ?? latest.data ?? latest);
}

function markerIcon() {
  return L.divIcon({
    className: "",
    html: '<span class="iot-marker"></span>',
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -18],
  });
}

function clusterIcon(cluster: L.MarkerCluster) {
  return L.divIcon({
    className: "",
    html: `<span class="iot-cluster">${cluster.getChildCount()}</span>`,
    iconSize: [42, 42],
    iconAnchor: [21, 21],
  });
}

function popupHtml(node: NodeWithCoords): string {
  return `
    <div class="iot-popup">
      <strong>${escapeHtml(node.nome)}</strong>
      <div class="iot-popup-grid">
        <span><b>Codigo:</b> ${escapeHtml(node.codigo)}</span>
        <span><b>Ultima sincronizacao:</b> ${escapeHtml(formatDate(node.ultimo_sync_em))}</span>
        <span><b>Dispositivos:</b> ${node.dispositivos.length}</span>
      </div>
    </div>
  `;
}

function ClusterLayer({
  nodes,
  onSelect,
}: {
  nodes: NodeWithCoords[];
  onSelect: (nodeId: string) => void;
}) {
  const map = useMap();

  useEffect(() => {
    const group = L.markerClusterGroup({
      iconCreateFunction: clusterIcon,
      showCoverageOnHover: false,
      maxClusterRadius: 48,
    });

    nodes.forEach((node) => {
      L.marker([node.lat, node.lng], { icon: markerIcon() })
        .bindPopup(popupHtml(node))
        .on("click", () => onSelect(node.id))
        .addTo(group);
    });

    group.addTo(map);
    if (nodes.length > 0) {
      map.fitBounds(group.getBounds(), { padding: [48, 48], maxZoom: 17 });
    } else {
      map.setView(UFMA_CENTER, 15);
    }

    return () => {
      group.removeFrom(map);
    };
  }, [nodes, map, onSelect]);

  return null;
}

function statusText(total: number, valid: number) {
  if (total === 0) return "Nenhum no de borda publicado";
  if (valid === total) return `${valid} nos de borda no mapa`;
  return `${valid} de ${total} nos de borda com coordenadas`;
}

export function PublicMapPage({ embedded = false }: PublicMapPageProps) {
  const [nodes, setNodes] = useState<NoBordaMapa[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedDevice, setSelectedDevice] =
    useState<DispositivoStatus | null>(null);
  const [deviceHistory, setDeviceHistory] =
    useState<DispositivoHistorico | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const navigate = useNavigate();

  const nodesWithCoords = useMemo(() => parseNodes(nodes), [nodes]);
  const selectedNode = useMemo(() => {
    return nodes.find((node) => node.id === selectedNodeId) || nodes[0] || null;
  }, [nodes, selectedNodeId]);

  async function loadNodes() {
    setLoading(true);
    setError("");
    try {
      const response = await apiFetch<NoBordaMapa[]>("/public/mapa/nos/", {
        skipAuth: true,
      });
      setNodes(response);
      setSelectedNodeId((current) =>
        current && response.some((node) => node.id === current)
          ? current
          : response[0]?.id || null,
      );
      setUpdatedAt(new Date().toLocaleString("pt-BR"));
    } catch (err) {
      setError(detalheErro(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadDeviceHistory(device: DispositivoStatus) {
    setSelectedDevice(device);
    setDeviceHistory(null);
    setHistoryError("");
    if (!device.interscity_uuid) return;

    setHistoryLoading(true);
    try {
      const response = await apiFetch<DispositivoHistorico>(
        `/public/mapa/dispositivos/${device.id}/historico/?dias=1`,
        {
          skipAuth: true,
        },
      );
      setDeviceHistory(response);
    } catch (err) {
      setHistoryError(detalheErro(err));
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    void loadNodes();
  }, []);

  useEffect(() => {
    if (embedded) return;
    let active = true;

    async function redirectAuthenticated() {
      try {
        const me = await carregarSessaoAutenticada();
        if (active && me) navigate("/app/mapa-iot", { replace: true });
      } catch {
        // A rota publica deve continuar acessivel para visitantes.
      }
    }

    void redirectAuthenticated();
    return () => {
      active = false;
    };
  }, [embedded, navigate]);

  useEffect(() => {
    setSelectedDevice(null);
    setDeviceHistory(null);
    setHistoryError("");
  }, [selectedNodeId]);

  const content = (
    <section className={embedded ? "map-shell-wrapper" : "public-wrapper"}>
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <div className="page-pretitle">Geo</div>
            <h1 className="page-title">Mapa IoT</h1>
            <p className="page-description">
              Nós de borda aparecem no mapa abaixo. Eles são centrais de
              processamento e reconhecimento facial que agem como intermediários
              entre a API e os dispositivos AutoPonto.
            </p>
          </div>
          <div className="page-actions">
            <Button
              onClick={() => void loadNodes()}
              disabled={loading}
              variant="secondary"
            >
              {loading ? "Atualizando..." : "Atualizar"}
            </Button>
          </div>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="row col-8-4">
        <div className="card map-card">
          <MapContainer center={UFMA_CENTER} zoom={15} className="iot-map">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <ClusterLayer
              nodes={nodesWithCoords}
              onSelect={setSelectedNodeId}
            />
          </MapContainer>
          {loading && (
            <div className="map-state">Carregando nos de borda...</div>
          )}
          {!loading && nodesWithCoords.length === 0 && !error && (
            <div className="map-state">
              Nenhum no de borda com coordenadas cadastrado.
            </div>
          )}
        </div>

        <aside className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Nos de borda</div>
              <div className="card-subtitle">
                {statusText(nodes.length, nodesWithCoords.length)}
              </div>
            </div>
          </div>
          <div className="card-body map-status-list">
            <div className="device-meta">
              {updatedAt
                ? `Atualizado em ${updatedAt}`
                : "Aguardando atualizacao"}
            </div>
            {!selectedNode && (
              <div className="empty-card-description">
                Selecione um nó no mapa para ver detalhes e dispositivos
                associados.
              </div>
            )}
            {selectedNode && (
              <>
                <div className="node-summary">
                  <span className="device-dot" />
                  <span>
                    <span className="device-name">
                      {selectedNode.nome || selectedNode.codigo}
                    </span>
                    <span className="device-meta">{selectedNode.codigo}</span>
                    <span className="device-meta">
                      Ultima sincronizacao:{" "}
                      {formatDate(selectedNode.ultimo_sync_em)}
                    </span>
                  </span>
                </div>

                <div className="divider-label">Dispositivos</div>
                {selectedNode.dispositivos.length === 0 && (
                  <div className="empty-card-description">
                    Este no ainda nao possui dispositivos ativos.
                  </div>
                )}
                {selectedNode.dispositivos.map((device) => (
                  <button
                    type="button"
                    key={device.id}
                    className={`device-row device-row-button ${selectedDevice?.id === device.id ? "active" : ""}`}
                    onClick={() => void loadDeviceHistory(device)}
                  >
                    <span className="device-dot" />
                    <span>
                      <span className="device-name">
                        {device.nome || device.codigo}
                      </span>
                      <span className="device-meta">
                        {device.codigo} - {device.sala || "Sem sala"}
                      </span>
                      <span className="device-meta">
                        {device.interscity_uuid
                          ? "Telemetria IntersCity"
                          : "Sem UUID IntersCity"}
                      </span>
                    </span>
                  </button>
                ))}
              </>
            )}
          </div>
        </aside>
      </div>

      <section className="card device-dashboard-card">
        <div className="card-header">
          <div>
            <div className="card-title">Dashboard do dispositivo</div>
            <div className="card-subtitle">
              {selectedDevice
                ? `${selectedDevice.nome || selectedDevice.codigo} - ${selectedDevice.codigo}`
                : "Selecione um dispositivo do no"}
            </div>
          </div>
        </div>
        <div className="card-body">
          {!selectedDevice && (
            <div className="empty-card-description">
              As capacidades recuperadas do IntersCity aparecem aqui.
            </div>
          )}
          {selectedDevice && !selectedDevice.interscity_uuid && (
            <div className="alert alert-error">
              Este dispositivo ainda nao possui UUID IntersCity para consulta de
              metricas.
            </div>
          )}
          {historyError && (
            <div className="alert alert-error">{historyError}</div>
          )}
          {historyLoading && (
            <div className="empty-card-description">
              Carregando metricas do dispositivo...
            </div>
          )}
          {selectedDevice &&
            selectedDevice.interscity_uuid &&
            !historyLoading && (
              <div className="metrics-grid">
                {METRICS.map(([key, label]) => (
                  <div className="metric-card" key={key}>
                    <span className="metric-label">{label}</span>
                    <strong className="metric-value">
                      {metricValue(deviceHistory, key)}
                    </strong>
                  </div>
                ))}
              </div>
            )}
        </div>
      </section>
    </section>
  );

  return (
    <>
      <PageMeta
        title="Mapa IoT | AutoPonto"
        description="Mapa publico de dispositivos IoT AutoPonto."
      />
      {embedded ? (
        content
      ) : (
        <main className="public-page">
          <header className="public-topbar">
            <div className="public-topbar-inner">
              <Link to="/">
                <BrandLogo size="sm" />
              </Link>
              <div className="public-actions">
                <ThemeToggleButton />
                <Link to="/signin" className="btn btn-outline">
                  Entrar
                </Link>
              </div>
            </div>
          </header>
          {content}
        </main>
      )}
    </>
  );
}
