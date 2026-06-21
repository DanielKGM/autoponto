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

function escapeHtml(value: string | null): string {
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
    <div style="min-width: 220px">
      <strong style="display:block;font-size:14px;margin-bottom:6px">${escapeHtml(device.nome)}</strong>
      <div style="display:grid;gap:4px;font-size:12px;color:#475467">
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
      <main className="min-h-[100dvh] bg-gray-50 dark:bg-gray-950">
        <header className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
          <div className="mx-auto flex max-w-[1536px] items-center justify-between gap-4 px-4 py-4 md:px-6">
            <Link to="/">
              <BrandLogo size="sm" />
            </Link>
            <div className="flex items-center gap-3">
              <ThemeToggleButton />
              <Link to="/signin" className="hidden rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-theme-xs hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-white/5 sm:inline-flex">
                Entrar
              </Link>
            </div>
          </div>
        </header>
        <section className="mx-auto grid max-w-[1536px] gap-4 p-4 md:p-6">
          <div className="flex flex-col justify-between gap-4 rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] md:flex-row md:items-center">
            <div>
              <h1 className="text-lg font-semibold text-gray-800 dark:text-white/90">Mapa IoT</h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Dispositivos ESP32 cadastrados com coordenadas publicas.</p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-sm text-gray-500 dark:text-gray-400">{updatedAt ? `Atualizado em ${updatedAt}` : "Aguardando atualizacao"}</span>
              <Button onClick={() => void loadDevices()} disabled={loading} variant="secondary">
                {loading ? "Atualizando..." : "Atualizar"}
              </Button>
            </div>
          </div>
          {error && <div className="rounded-xl border border-error-500/20 bg-error-50 px-4 py-3 text-sm font-medium text-error-500">{error}</div>}
          <div className="relative min-h-[640px] overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
            <MapContainer center={UFMA_CENTER} zoom={15} className="h-[640px] min-h-[640px]">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <ClusterLayer devices={devicesWithCoords} />
            </MapContainer>
            {!loading && devicesWithCoords.length === 0 && !error && (
              <div className="pointer-events-none absolute inset-x-4 top-4 z-[500] rounded-xl border border-gray-200 bg-white/95 px-4 py-3 text-sm font-medium text-gray-500 shadow-theme-sm backdrop-blur dark:border-gray-800 dark:bg-gray-900/95 dark:text-gray-400">
                Nenhum dispositivo com coordenadas cadastrado.
              </div>
            )}
          </div>
        </section>
      </main>
    </>
  );
}
