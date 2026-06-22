import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import L from "leaflet";
import "leaflet.markercluster";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { apiFetch, detalheErro } from "../api";
import { BrandLogo } from "../components/common/BrandLogo";
import { PageMeta } from "../components/common/PageMeta";
import { ThemeToggleButton } from "../components/common/ThemeToggleButton";
import { Button } from "../components/ui/Button";
import type { DispositivoStatus } from "../types";

type DeviceWithCoords = DispositivoStatus & {
  lat: number;
  lng: number;
};

const UFMA_CENTER: [number, number] = [-2.5583, -44.3077];

function parseDevices(devices: DispositivoStatus[]): DeviceWithCoords[] {
  return devices.flatMap((device) => {
    const lat = Number(device.latitude);
    const lng = Number(device.longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return [];
    return [{ ...device, lat, lng }];
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

function popupHtml(device: DeviceWithCoords): string {
  return `
    <div class="iot-popup">
      <strong>${escapeHtml(device.nome)}</strong>
      <div class="iot-popup-grid">
        <span><b>Codigo:</b> ${escapeHtml(device.codigo)}</span>
        <span><b>Sala:</b> ${escapeHtml(device.sala)}</span>
        <span><b>Predio:</b> ${escapeHtml(device.predio)}</span>
        <span><b>UUID:</b> ${escapeHtml(device.interscity_uuid)}</span>
      </div>
    </div>
  `;
}

function ClusterLayer({ devices }: { devices: DeviceWithCoords[] }) {
  const map = useMap();

  useEffect(() => {
    const group = L.markerClusterGroup({
      iconCreateFunction: clusterIcon,
      showCoverageOnHover: false,
      maxClusterRadius: 48,
    });

    devices.forEach((device) => {
      L.marker([device.lat, device.lng], { icon: markerIcon() }).bindPopup(popupHtml(device)).addTo(group);
    });

    group.addTo(map);
    if (devices.length > 0) {
      map.fitBounds(group.getBounds(), { padding: [48, 48], maxZoom: 17 });
    } else {
      map.setView(UFMA_CENTER, 15);
    }

    return () => {
      group.removeFrom(map);
    };
  }, [devices, map]);

  return null;
}

function statusText(total: number, valid: number) {
  if (total === 0) return "Nenhum dispositivo publicado";
  if (valid === total) return `${valid} dispositivos no mapa`;
  return `${valid} de ${total} dispositivos com coordenadas`;
}

export function PublicMapPage() {
  const [devices, setDevices] = useState<DispositivoStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const devicesWithCoords = useMemo(() => parseDevices(devices), [devices]);

  async function loadDevices() {
    setLoading(true);
    setError("");
    try {
      const response = await apiFetch<DispositivoStatus[]>("/public/mapa/dispositivos/", { skipAuth: true });
      setDevices(response);
      setUpdatedAt(new Date().toLocaleString("pt-BR"));
    } catch (err) {
      setError(detalheErro(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDevices();
  }, []);

  return (
    <>
      <PageMeta title="Mapa IoT | AutoPonto" description="Mapa publico de dispositivos IoT AutoPonto." />
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

        <section className="public-wrapper">
          <div className="page-header">
            <div className="page-header-row">
              <div>
                <div className="page-pretitle">Geo</div>
                <h1 className="page-title">Mapa IoT</h1>
                <p className="page-description">Dispositivos ESP32 cadastrados com coordenadas publicas.</p>
              </div>
              <div className="page-actions">
                <Button onClick={() => void loadDevices()} disabled={loading} variant="secondary">
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
                <ClusterLayer devices={devicesWithCoords} />
              </MapContainer>
              {loading && <div className="map-state">Carregando dispositivos...</div>}
              {!loading && devicesWithCoords.length === 0 && !error && (
                <div className="map-state">Nenhum dispositivo com coordenadas cadastrado.</div>
              )}
            </div>

            <aside className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Dispositivos</div>
                  <div className="card-subtitle">{statusText(devices.length, devicesWithCoords.length)}</div>
                </div>
              </div>
              <div className="card-body map-status-list">
                <div className="device-meta">{updatedAt ? `Atualizado em ${updatedAt}` : "Aguardando atualizacao"}</div>
                {!loading && devicesWithCoords.length === 0 && (
                  <div className="empty-card-description">A lista sera preenchida quando houver dispositivos com latitude e longitude.</div>
                )}
                {devicesWithCoords.slice(0, 8).map((device) => (
                  <div key={device.id} className="device-row">
                    <span className="device-dot" />
                    <span>
                      <span className="device-name">{device.nome || device.codigo}</span>
                      <span className="device-meta">
                        {device.codigo} - {device.sala || "Sem sala"}
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </aside>
          </div>
        </section>
      </main>
    </>
  );
}
