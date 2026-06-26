import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Link, useNavigate } from "react-router";
import L from "leaflet";
import "leaflet.markercluster";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import type { EChartsOption } from "echarts";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { publicAssetPath } from "../../../shared/assets";
import {
  apiFetch,
  carregarSessaoAutenticada,
  detalheErro,
} from "../../../shared/api";
import { BrandLogo } from "../../../shared/ui/BrandLogo";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { LoadingDots } from "../../../shared/ui/LoadingDots";
import { PageMeta } from "../../../shared/ui/PageMeta";
import { Popover } from "../../../shared/ui/Popover";
import { ThemeToggleButton } from "../../../shared/ui/ThemeToggleButton";
import {
  ActivityIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  MaximizeIcon,
  MemoryIcon,
  MinimizeIcon,
  RefreshIcon,
  SignalIcon,
} from "../../../shared/ui/icons";
import type {
  DispositivoHistorico,
  DispositivoStatus,
  NoBordaMapa,
} from "../../../shared/types";

type PublicMapPageProps = {
  embedded?: boolean;
};

type NodeWithCoords = NoBordaMapa & {
  lat: number;
  lng: number;
};

type CapabilitySample = Record<string, unknown>;
type TelemetryPeriod = "recentes" | "2h" | "1d";

type CapabilityDefinition = {
  key: string;
  label: string;
  formatter?: (value: unknown) => string;
};

type ChartSeries = {
  name: string;
  color: string;
  data: Array<[number, number]>;
};

type RecentStatDefinition = CapabilityDefinition & {
  description: string;
  icon: "activity" | "memory" | "signal";
  tone: "teal" | "blue" | "green" | "yellow" | "red";
};

const UFMA_CENTER: [number, number] = [-2.5583, -44.3077];
const EDGE_NODE_ICON_URL = publicAssetPath("images/edge-node-marker.svg");
const EChart = lazy(() =>
  import("../../../shared/ui/EChart").then((module) => ({
    default: module.EChart,
  })),
);

const PERIOD_OPTIONS: Array<{ value: TelemetryPeriod; label: string }> = [
  { value: "recentes", label: "Recentes" },
  { value: "2h", label: "2 horas" },
  { value: "1d", label: "1 dia" },
];

const CAPABILITY_DEFINITIONS: CapabilityDefinition[] = [
  { key: "status", label: "Status" },
  { key: "presenca", label: "PIR" },
  { key: "heap_free", label: "Heap livre", formatter: formatBytes },
  { key: "heap_min", label: "Piso heap", formatter: formatBytes },
  { key: "heap_max", label: "Bloco heap", formatter: formatBytes },
  { key: "psram_free", label: "PSRAM livre", formatter: formatBytes },
  { key: "psram_min", label: "Piso PSRAM", formatter: formatBytes },
  { key: "psram_max", label: "Bloco PSRAM", formatter: formatBytes },
  { key: "rssi", label: "Sinal Wi-Fi", formatter: formatRssi },
  { key: "post_max_ms", label: "Pico envio", formatter: formatMs },
];

const RECENT_STAT_CARDS: RecentStatDefinition[] = [
  {
    key: "heap_free",
    label: "Heap livre",
    description: "Memória interna disponível para novas operações.",
    formatter: formatBytes,
    icon: "memory",
    tone: "teal",
  },
  {
    key: "heap_min",
    label: "Piso heap",
    description: "Menor memória interna livre observada recentemente.",
    formatter: formatBytes,
    icon: "memory",
    tone: "blue",
  },
  {
    key: "heap_max",
    label: "Bloco heap",
    description: "Maior bloco contínuo disponível na memória interna.",
    formatter: formatBytes,
    icon: "memory",
    tone: "green",
  },
  {
    key: "psram_free",
    label: "PSRAM livre",
    description: "Memória externa disponível para buffers maiores.",
    formatter: formatBytes,
    icon: "memory",
    tone: "teal",
  },
  {
    key: "psram_min",
    label: "Piso PSRAM",
    description: "Menor memória externa livre observada recentemente.",
    formatter: formatBytes,
    icon: "memory",
    tone: "blue",
  },
  {
    key: "psram_max",
    label: "Bloco PSRAM",
    description: "Maior bloco contínuo disponível na memória externa.",
    formatter: formatBytes,
    icon: "memory",
    tone: "green",
  },
  {
    key: "rssi",
    label: "Sinal Wi-Fi",
    description:
      "Potência do sinal recebido. Valores menos negativos indicam sinal melhor.",
    formatter: formatRssi,
    icon: "signal",
    tone: "yellow",
  },
  {
    key: "post_max_ms",
    label: "Pico envio",
    description: "Maior duração recente de envio HTTP para o servidor.",
    formatter: formatMs,
    icon: "activity",
    tone: "red",
  },
];

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
  if (!value) return "Não sincronizado";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR");
}

function formatShortDate(value: string | null | undefined) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function toFiniteNumber(value: unknown): number | null {
  if (Array.isArray(value)) return toFiniteNumber(value[1]);
  if (typeof value === "boolean") return value ? 1 : 0;
  const numberValue =
    typeof value === "number"
      ? value
      : typeof value === "string"
        ? Number(value)
        : Number.NaN;
  return Number.isFinite(numberValue) ? numberValue : null;
}

function formatMetric(value: unknown) {
  if (Array.isArray(value)) return formatMetric(value[1]);
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "number") return value.toLocaleString("pt-BR");
  if (typeof value === "string") return value;
  if (typeof value === "boolean") return value ? "Sim" : "Não";
  return JSON.stringify(value);
}

function formatBytes(value: unknown) {
  const numberValue = toFiniteNumber(value);
  if (numberValue === null) return formatMetric(value);
  if (Math.abs(numberValue) >= 1024 * 1024) {
    return `${(numberValue / 1024 / 1024).toLocaleString("pt-BR", {
      maximumFractionDigits: 1,
    })} MB`;
  }
  if (Math.abs(numberValue) >= 1024) {
    return `${(numberValue / 1024).toLocaleString("pt-BR", {
      maximumFractionDigits: 1,
    })} KB`;
  }
  return `${numberValue.toLocaleString("pt-BR")} B`;
}

function formatMs(value: unknown) {
  const numberValue = toFiniteNumber(value);
  if (numberValue === null) return formatMetric(value);
  return `${numberValue.toLocaleString("pt-BR")} ms`;
}

function formatRssi(value: unknown) {
  const numberValue = toFiniteNumber(value);
  if (numberValue === null) return formatMetric(value);
  return `${numberValue.toLocaleString("pt-BR")} dBm`;
}

function sampleValue(sample: CapabilitySample | undefined) {
  if (!sample) return undefined;
  if ("value" in sample) return sample.value;
  if ("valor" in sample) return sample.valor;
  return undefined;
}

function sampleDate(sample: CapabilitySample | undefined) {
  if (!sample) return undefined;
  const value = sample.date ?? sample.data ?? sample.timestamp;
  return typeof value === "string" ? value : undefined;
}

function latestSample(
  history: DispositivoHistorico | null,
  key: string,
): CapabilitySample | undefined {
  const latest = history?.ultimo?.[key];
  if (latest) return latest;
  const values = history?.historico?.[key] || [];
  return values.length > 0 ? values[values.length - 1] : undefined;
}

function numericSeries(history: DispositivoHistorico | null, key: string) {
  const values = history?.historico?.[key] || [];
  return values
    .flatMap((sample) => {
      const numberValue = toFiniteNumber(sampleValue(sample));
      const dateValue = sampleDate(sample);
      const timeValue = dateValue ? Date.parse(dateValue) : Number.NaN;
      if (numberValue === null || !Number.isFinite(timeValue)) return [];
      return [[timeValue, numberValue] as [number, number]];
    })
    .sort((left, right) => left[0] - right[0]);
}

function breakGapMs(period: TelemetryPeriod) {
  if (period === "2h") return 10 * 60 * 1000;
  if (period === "1d") return 2 * 60 * 60 * 1000;
  return Number.POSITIVE_INFINITY;
}

function seriesWithTimeBreaks(
  data: Array<[number, number]>,
  period: TelemetryPeriod,
): Array<[number, number | null]> {
  const gapMs = breakGapMs(period);
  if (!Number.isFinite(gapMs) || data.length < 2) return data;

  const points: Array<[number, number | null]> = [];
  data.forEach((point, index) => {
    points.push(point);
    const nextPoint = data[index + 1];
    if (!nextPoint || nextPoint[0] - point[0] <= gapMs) return;

    const breakStart = point[0] + 1;
    const breakEnd = nextPoint[0] - 1;
    if (breakEnd > breakStart) {
      points.push([breakStart, null], [breakEnd, null]);
    }
  });

  return points;
}

function bucketMinutesLabel(minutes: number | undefined) {
  if (!minutes) return "baldes";
  if (minutes >= 60) {
    const hours = minutes / 60;
    return hours === 1 ? "baldes de 1 hora" : `baldes de ${hours} horas`;
  }
  return `baldes de ${minutes} min`;
}

function localPirBuckets(
  history: DispositivoHistorico | null,
  period: TelemetryPeriod,
) {
  const serverBuckets = history?.pir?.baldes || [];
  if (serverBuckets.length > 0) return serverBuckets;

  const events = history?.pir?.eventos || [];
  const parsedEvents = events
    .flatMap((event) => {
      const timestamp = Date.parse(event.timestamp);
      if (!Number.isFinite(timestamp)) return [];
      return [{ timestamp, active: Boolean(event.valor) }];
    })
    .sort((left, right) => left.timestamp - right.timestamp);

  if (parsedEvents.length === 0) return [];

  const bucketMs = (period === "1d" ? 60 : 10) * 60 * 1000;
  const start = Math.floor(parsedEvents[0].timestamp / bucketMs) * bucketMs;
  const end =
    Math.floor(parsedEvents[parsedEvents.length - 1].timestamp / bucketMs) *
    bucketMs;
  const buckets = [];

  for (let cursor = start; cursor <= end; cursor += bucketMs) {
    const next = cursor + bucketMs;
    buckets.push({
      inicio: new Date(cursor).toISOString(),
      fim: new Date(next).toISOString(),
      quantidade: parsedEvents.filter(
        (event) =>
          event.active && event.timestamp >= cursor && event.timestamp < next,
      ).length,
    });
  }

  return buckets;
}

function latestDate(history: DispositivoHistorico | null) {
  const timestamps = CAPABILITY_DEFINITIONS.flatMap((definition) => {
    const dateValue = sampleDate(latestSample(history, definition.key));
    return dateValue ? [dateValue] : [];
  });
  if (timestamps.length === 0) return null;
  return timestamps.sort((a, b) => Date.parse(b) - Date.parse(a))[0];
}

function chipClass(value: unknown) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("online") || normalized === "ok") return "chip-green";
  if (normalized.includes("offline") || normalized.includes("erro"))
    return "chip-red";
  if (normalized.includes("timeout") || normalized.includes("indisponivel"))
    return "chip-yellow";
  return "chip-muted";
}

function statusLabel(value: unknown, fallback: string) {
  const formatted = formatMetric(value);
  return formatted === "-" ? fallback : formatted;
}

function hasSeriesData(series: ChartSeries[]) {
  return series.some((item) => item.data.length > 0);
}

function telemetryDataZoom(): EChartsOption["dataZoom"] {
  return [
    {
      type: "inside",
      xAxisIndex: 0,
      filterMode: "none",
      zoomOnMouseWheel: true,
      moveOnMouseMove: true,
      moveOnMouseWheel: false,
    },
    {
      type: "slider",
      xAxisIndex: 0,
      filterMode: "none",
      height: 18,
      bottom: 8,
      showDetail: false,
      brushSelect: false,
    },
  ];
}

function lineChartOption(
  series: ChartSeries[],
  formatter: (value: unknown) => string,
  period: TelemetryPeriod,
  axisLabelFormatter?: (value: number) => string,
): EChartsOption {
  return {
    color: series.map((item) => item.color),
    tooltip: {
      trigger: "axis",
      valueFormatter: formatter,
    },
    legend: {
      top: 0,
      textStyle: { color: "#7e8896", fontSize: 11 },
    },
    grid: {
      top: 38,
      right: 16,
      bottom: 52,
      left: 46,
    },
    dataZoom: telemetryDataZoom(),
    xAxis: {
      type: "time",
      axisLabel: { color: "#7e8896" },
      axisLine: { lineStyle: { color: "#e6e7eb" } },
      splitLine: { show: false },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#7e8896", formatter: axisLabelFormatter },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: "#eff0f3", type: "dashed" } },
    },
    series: series.map((item) => ({
      name: item.name,
      type: "line",
      smooth: true,
      connectNulls: false,
      showSymbol: item.data.length <= 8,
      symbolSize: 6,
      areaStyle: { opacity: 0.06 },
      lineStyle: { width: 2 },
      data: seriesWithTimeBreaks(item.data, period),
    })),
  };
}

function networkRainfallChartOption(
  postMaxSeries: Array<[number, number]>,
  rssiSeries: Array<[number, number]>,
  period: TelemetryPeriod,
): EChartsOption {
  const postData = seriesWithTimeBreaks(postMaxSeries, period);
  const rssiData = seriesWithTimeBreaks(rssiSeries, period);

  return {
    color: ["#d63939", "#4299e1"],
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      formatter: (params: any) => {
        const items = Array.isArray(params) ? params : [params];
        const first = items[0];
        const timestamp = Array.isArray(first?.value)
          ? first.value[0]
          : first?.axisValue;

        const numericTimestamp = Number(timestamp);
        const title = Number.isFinite(numericTimestamp)
          ? formatShortDate(new Date(numericTimestamp).toISOString())
          : "-";

        const lines = items
          .map((item) => {
            const value = Array.isArray(item.value)
              ? item.value[1]
              : item.value;

            const numericValue = toFiniteNumber(value);
            if (numericValue === null) return null;

            if (item.seriesName === "RSSI") {
              return `${item.marker || ""}RSSI: ${formatRssi(numericValue)}`;
            }

            return `${item.marker || ""}Tempo máximo de POST: ${formatMs(
              numericValue,
            )}`;
          })
          .filter(Boolean);

        return [title, ...lines].join("<br/>");
      },
    },
    legend: {
      top: 0,
      textStyle: { color: "#7e8896", fontSize: 11 },
    },
    grid: {
      top: 42,
      right: 58,
      bottom: 58,
      left: 56,
    },
    dataZoom: telemetryDataZoom(),
    xAxis: {
      type: "time",
      axisLabel: { color: "#7e8896" },
      axisLine: { lineStyle: { color: "#e6e7eb" } },
      splitLine: { show: false },
    },
    yAxis: [
      {
        type: "value",
        name: "POST máx.",
        min: 0,
        axisLabel: {
          color: "#7e8896",
          formatter: (value: number) => `${value} ms`,
        },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: "#eff0f3", type: "dashed" } },
      },
      {
        type: "value",
        name: "RSSI",
        scale: true,
        axisLabel: {
          color: "#7e8896",
          formatter: (value: number) => `${value} dBm`,
        },
        axisLine: { show: false },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: "Tempo máximo de POST",
        type: "bar",
        yAxisIndex: 0,
        barMaxWidth: 22,
        data: postData,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
        },
      },
      {
        name: "RSSI",
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        connectNulls: false,
        showSymbol: rssiSeries.length <= 12,
        symbolSize: 6,
        lineStyle: { width: 2 },
        data: rssiData,
      },
    ],
  };
}

function pirHistogramChartOption(
  history: DispositivoHistorico | null,
  period: TelemetryPeriod,
): EChartsOption {
  const buckets = localPirBuckets(history, period);
  return {
    color: ["#1abb9c"],
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params: any) => {
        const item = Array.isArray(params) ? params[0] : params;
        const bucket = buckets[item.dataIndex];
        return `${formatShortDate(bucket?.inicio)}<br/>Detecções: ${item.value}`;
      },
    },
    grid: { top: 18, right: 16, bottom: 34, left: 38 },
    xAxis: {
      type: "category",
      data: buckets.map((bucket) => formatShortDate(bucket.inicio)),
      axisLabel: { color: "#7e8896", fontSize: 10 },
      axisLine: { lineStyle: { color: "#e6e7eb" } },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      minInterval: 1,
      axisLabel: { color: "#7e8896" },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: "#eff0f3", type: "dashed" } },
    },
    series: [
      {
        name: "Detecções",
        type: "bar",
        barWidth: "52%",
        data: buckets.map((bucket) => ({
          value: bucket.quantidade,
          itemStyle: { borderRadius: [4, 4, 0, 0] },
        })),
      },
    ],
  };
}

function TelemetryChart({ option }: { option: EChartsOption }) {
  return (
    <Suspense
      fallback={
        <div className="chart-loading">
          <LoadingDots label="Carregando gráfico" />
        </div>
      }
    >
      <EChart option={option} />
    </Suspense>
  );
}

function StatCardIcon({ icon }: { icon: RecentStatDefinition["icon"] }) {
  if (icon === "signal") return <SignalIcon />;
  if (icon === "activity") return <ActivityIcon />;
  return <MemoryIcon />;
}

function markerIcon() {
  return L.icon({
    iconUrl: EDGE_NODE_ICON_URL,
    className: "iot-marker-icon",
    iconSize: [46, 46],
    iconAnchor: [23, 42],
    popupAnchor: [0, -38],
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
        <span><b>Última sincronização:</b> ${escapeHtml(formatDate(node.ultimo_sync_em))}</span>
        <span><b>Dispositivos:</b> ${node.dispositivos.length}</span>
      </div>
    </div>
  `;
}

function ResizeMapOnChange({ expanded }: { expanded: boolean }) {
  const map = useMap();

  useEffect(() => {
    const timeout = window.setTimeout(() => map.invalidateSize(), 260);
    return () => window.clearTimeout(timeout);
  }, [expanded, map]);

  return null;
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
  if (total === 0) return "Nenhum nó de borda publicado";
  if (valid === total) return `${valid} nó(s) de borda no mapa`;
  return `${valid} de ${total} nós de borda com coordenadas`;
}

export function PublicMapPage({ embedded = false }: PublicMapPageProps) {
  const [nodes, setNodes] = useState<NoBordaMapa[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedDevice, setSelectedDevice] =
    useState<DispositivoStatus | null>(null);
  const [selectedPeriod, setSelectedPeriod] =
    useState<TelemetryPeriod>("recentes");
  const [deviceHistory, setDeviceHistory] =
    useState<DispositivoHistorico | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [mapExpanded, setMapExpanded] = useState(false);
  const [mapCollapsed, setMapCollapsed] = useState(false);
  const [dashboardCollapsed, setDashboardCollapsed] = useState(false);
  const dashboardRef = useRef<HTMLElement | null>(null);
  const navigate = useNavigate();

  const nodesWithCoords = useMemo(() => parseNodes(nodes), [nodes]);
  const selectedNode = useMemo(() => {
    return nodes.find((node) => node.id === selectedNodeId) || nodes[0] || null;
  }, [nodes, selectedNodeId]);

  const loadNodes = useCallback(async () => {
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
  }, []);

  const selectNode = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId);
  }, []);

  const selectDevice = useCallback((device: DispositivoStatus) => {
    setSelectedDevice(device);
    setDashboardCollapsed(false);
    requestAnimationFrame(() => {
      dashboardRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }, []);

  const loadDeviceHistory = useCallback(async () => {
    if (!selectedDevice) return;

    setDeviceHistory(null);
    setHistoryError("");
    if (!selectedDevice.interscity_uuid) return;

    setHistoryLoading(true);
    try {
      const response = await apiFetch<DispositivoHistorico>(
        `/public/mapa/dispositivos/${selectedDevice.id}/historico/?periodo=${selectedPeriod}`,
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
  }, [selectedDevice, selectedPeriod]);

  useEffect(() => {
    void loadNodes();
  }, [loadNodes]);

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

  useEffect(() => {
    void loadDeviceHistory();
  }, [loadDeviceHistory]);

  const heapSeries = useMemo<ChartSeries[]>(
    () => [
      {
        name: "Livre",
        color: "#1abb9c",
        data: numericSeries(deviceHistory, "heap_free"),
      },
      {
        name: "Piso",
        color: "#4299e1",
        data: numericSeries(deviceHistory, "heap_min"),
      },
      {
        name: "Maior bloco",
        color: "#2fb344",
        data: numericSeries(deviceHistory, "heap_max"),
      },
    ],
    [deviceHistory],
  );

  const psramSeries = useMemo<ChartSeries[]>(
    () => [
      {
        name: "Livre",
        color: "#1abb9c",
        data: numericSeries(deviceHistory, "psram_free"),
      },
      {
        name: "Piso",
        color: "#4299e1",
        data: numericSeries(deviceHistory, "psram_min"),
      },
      {
        name: "Maior bloco",
        color: "#2fb344",
        data: numericSeries(deviceHistory, "psram_max"),
      },
    ],
    [deviceHistory],
  );

  const networkPostSeries = useMemo(
    () => numericSeries(deviceHistory, "post_max_ms"),
    [deviceHistory],
  );

  const networkRssiSeries = useMemo(
    () => numericSeries(deviceHistory, "rssi"),
    [deviceHistory],
  );

  const heapChart = useMemo(
    () =>
      lineChartOption(heapSeries, formatBytes, selectedPeriod, (value) =>
        formatBytes(value),
      ),
    [heapSeries, selectedPeriod],
  );

  const psramChart = useMemo(
    () =>
      lineChartOption(psramSeries, formatBytes, selectedPeriod, (value) =>
        formatBytes(value),
      ),
    [psramSeries, selectedPeriod],
  );

  const signalChart = useMemo(
    () =>
      networkRainfallChartOption(
        networkPostSeries,
        networkRssiSeries,
        selectedPeriod,
      ),
    [networkPostSeries, networkRssiSeries, selectedPeriod],
  );

  const pirChart = useMemo(
    () => pirHistogramChartOption(deviceHistory, selectedPeriod),
    [deviceHistory, selectedPeriod],
  );

  const recentStats = useMemo(
    () =>
      RECENT_STAT_CARDS.flatMap((definition) => {
        const sample = latestSample(deviceHistory, definition.key);
        if (!sample) return [];
        return [
          {
            ...definition,
            value: definition.formatter
              ? definition.formatter(sampleValue(sample))
              : formatMetric(sampleValue(sample)),
            date: sampleDate(sample),
          },
        ];
      }),
    [deviceHistory],
  );

  const hasRecentData = recentStats.length > 0;
  const hasHeapData = hasSeriesData(heapSeries);
  const hasPsramData = hasSeriesData(psramSeries);
  const hasNetworkData =
    networkPostSeries.length > 0 || networkRssiSeries.length > 0;
  const hasPirData = localPirBuckets(deviceHistory, selectedPeriod).length > 0;
  const pirBucketMinutes =
    deviceHistory?.pir?.balde_minutos ?? (selectedPeriod === "1d" ? 60 : 10);
  const pirBucketLabel = bucketMinutesLabel(pirBucketMinutes);
  const isRecentPeriod = selectedPeriod === "recentes";
  const selectedPeriodLabel =
    PERIOD_OPTIONS.find((option) => option.value === selectedPeriod)?.label ||
    "Recentes";
  const freshness = latestDate(deviceHistory);
  const collectorStatus = deviceHistory?.collector_status || "-";
  const deviceStatus = sampleValue(latestSample(deviceHistory, "status"));

  const content = (
    <section className={embedded ? "map-shell-wrapper" : "public-wrapper"}>
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <div className="page-pretitle">Geo</div>
            <h1 className="page-title">Mapa IoT</h1>
            <p className="page-description">
              Dispositivos AutoPonto com telemetria operacional publicada no
              IntersCity.
            </p>
          </div>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div
        className={[
          "row col-8-4 map-layout",
          mapExpanded && "map-layout-expanded",
          mapCollapsed && "map-layout-collapsed",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <div className={`card map-card ${mapCollapsed ? "is-collapsed" : ""}`}>
          <div className="card-header map-card-header">
            <div>
              <div className="card-title">Mapa operacional</div>
              <div className="card-subtitle">
                {statusText(nodes.length, nodesWithCoords.length)}
              </div>
            </div>
            <div className="panel-actions">
              <button
                type="button"
                className="tb-btn"
                onClick={() => void loadNodes()}
                disabled={loading}
                aria-label="Atualizar mapa"
                data-tooltip={loading ? "Atualizando mapa" : "Atualizar mapa"}
              >
                <RefreshIcon />
              </button>
              <button
                type="button"
                className="tb-btn"
                onClick={() => setMapExpanded((current) => !current)}
                aria-label={mapExpanded ? "Compactar mapa" : "Expandir mapa"}
                data-tooltip={mapExpanded ? "Compactar mapa" : "Expandir mapa"}
              >
                {mapExpanded ? <MinimizeIcon /> : <MaximizeIcon />}
              </button>
              <button
                type="button"
                className="tb-btn"
                onClick={() => setMapCollapsed((current) => !current)}
                aria-label={mapCollapsed ? "Mostrar mapa" : "Recolher mapa"}
                data-tooltip={mapCollapsed ? "Mostrar mapa" : "Recolher mapa"}
              >
                {mapCollapsed ? <ChevronDownIcon /> : <ChevronUpIcon />}
              </button>
            </div>
          </div>

          {!mapCollapsed && (
            <div className="map-card-body">
              <MapContainer center={UFMA_CENTER} zoom={15} className="iot-map">
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <ResizeMapOnChange expanded={mapExpanded} />
                <ClusterLayer nodes={nodesWithCoords} onSelect={selectNode} />
              </MapContainer>
              {loading && (
                <div className="map-state">
                  <LoadingDots label="Carregando nós de borda" />
                </div>
              )}
              {!loading && nodesWithCoords.length === 0 && !error && (
                <div className="map-empty-state">
                  <EmptyState
                    title="Nenhum nó de borda no mapa"
                    text="Não há nós de borda com coordenadas geográficas para exibir no mapa."
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {!mapCollapsed && (
          <aside className="card map-side-card">
            <div className="card-header">
              <div>
                <div className="card-title">Nós de borda</div>
                <div className="card-subtitle">
                  {updatedAt
                    ? `Atualizado em ${updatedAt}`
                    : "Aguardando atualização"}
                </div>
              </div>
            </div>
            <div className="card-body map-status-list">
              {!selectedNode && (
                <EmptyState
                  title="Nenhum nó selecionado"
                  text="Selecione um nó no mapa para ver os dispositivos associados."
                />
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
                        Última sincronização:{" "}
                        {formatDate(selectedNode.ultimo_sync_em)}
                      </span>
                    </span>
                  </div>

                  <div className="divider-label">Dispositivos</div>
                  {selectedNode.dispositivos.length === 0 && (
                    <EmptyState
                      title="Sem dispositivos"
                      text="Este nó ainda não possui dispositivos ativos para selecionar."
                    />
                  )}
                  {selectedNode.dispositivos.map((device) => (
                    <button
                      type="button"
                      key={device.id}
                      className={`device-row device-row-button ${selectedDevice?.id === device.id ? "active" : ""}`}
                      onClick={() => selectDevice(device)}
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
        )}
      </div>

      <section
        ref={dashboardRef}
        className={`card device-dashboard-card ${dashboardCollapsed ? "is-collapsed" : ""}`}
      >
        <div className="card-header dashboard-card-header">
          <div>
            <div className="card-title">Métricas do dispositivo</div>
            <div className="card-subtitle">
              {selectedDevice
                ? `${selectedDevice.nome || selectedDevice.codigo}`
                : "Nenhum dispositivo selecionado"}
            </div>
          </div>
          <div className="dashboard-header-actions">
            <div className="chart-tabs" aria-label="Período de telemetria">
              {PERIOD_OPTIONS.map((option) => (
                <button
                  type="button"
                  key={option.value}
                  className={`chart-tab ${selectedPeriod === option.value ? "active" : ""}`}
                  onClick={() => setSelectedPeriod(option.value)}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <button
              type="button"
              className="tb-btn"
              onClick={() => void loadDeviceHistory()}
              disabled={!selectedDevice || historyLoading}
              aria-label="Atualizar dashboard"
              data-tooltip={
                historyLoading ? "Atualizando dashboard" : "Atualizar dashboard"
              }
            >
              <RefreshIcon />
            </button>
            <button
              type="button"
              className="tb-btn"
              onClick={() => setDashboardCollapsed((current) => !current)}
              aria-label={
                dashboardCollapsed ? "Mostrar dashboard" : "Recolher dashboard"
              }
              data-tooltip={
                dashboardCollapsed ? "Mostrar dashboard" : "Recolher dashboard"
              }
            >
              {dashboardCollapsed ? <ChevronDownIcon /> : <ChevronUpIcon />}
            </button>
          </div>
        </div>

        {!dashboardCollapsed && (
          <div className="card-body device-dashboard-body">
            {!selectedDevice && (
              <EmptyState
                title="Nenhum dispositivo selecionado"
                text="Selecione um dispositivo no mapa para ver as métricas de telemetria."
              />
            )}
            {selectedDevice && !selectedDevice.interscity_uuid && (
              <div className="alert alert-error">
                Este dispositivo ainda não possui UUID IntersCity para consulta
                de métricas.
              </div>
            )}
            {historyError && (
              <div className="alert alert-error">{historyError}</div>
            )}
            {historyLoading && (
              <div className="empty-card-description">
                <LoadingDots label="Carregando métricas do dispositivo" />
              </div>
            )}
            {selectedDevice &&
              selectedDevice.interscity_uuid &&
              !historyLoading && (
                <>
                  <div className="dashboard-meta-row">
                    <span
                      className={`chip ${chipClass(collectorStatus)}`}
                      tabIndex={0}
                    >
                      Collector: {collectorStatus}
                    </span>
                    <span
                      className={`chip ${chipClass(deviceStatus)}`}
                      data-tooltip="Último valor da capacidade status enviada pelo dispositivo."
                      tabIndex={0}
                    >
                      Status: {statusLabel(deviceStatus, "Sem status")}
                    </span>
                    <span
                      className="chip chip-green"
                      data-tooltip="Janela selecionada para consulta."
                      tabIndex={0}
                    >
                      Janela: {selectedPeriodLabel}
                    </span>
                    <span
                      className="chip chip-muted"
                      data-tooltip="Data mais recente entre as capacidades retornadas."
                      tabIndex={0}
                    >
                      Última amostra: {formatShortDate(freshness)}
                    </span>
                  </div>

                  {isRecentPeriod ? (
                    hasRecentData ? (
                      <div className="dashboard-kpi-grid recent-stats-grid">
                        {recentStats.map((stat) => (
                          <div className="telemetry-stat" key={stat.key}>
                            <div className={`stat-icon ${stat.tone}`}>
                              <StatCardIcon icon={stat.icon} />
                            </div>
                            <div className="stat-content">
                              <Popover
                                className="stat-popover"
                                title={stat.label}
                                text={stat.description}
                              >
                                <span className="stat-label stat-label-help">
                                  {stat.label}
                                </span>
                              </Popover>
                              <div className="stat-value-row">
                                <span className="stat-value">{stat.value}</span>
                              </div>
                              <div className="stat-subtext">
                                {formatShortDate(stat.date)}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <EmptyState
                        title="Sem dados recentes"
                        text="O Collector não retornou amostras recentes para este dispositivo."
                      />
                    )
                  ) : (
                    <div className="dashboard-chart-grid dashboard-chart-grid-history">
                      <div className="dashboard-panel">
                        <div className="dashboard-panel-header">
                          <div>
                            <div className="card-title">Heap</div>
                            <div className="card-subtitle">
                              Livre, piso e maior bloco.
                            </div>
                          </div>
                        </div>
                        <div className="chart-area chart-area-lg">
                          {hasHeapData ? (
                            <TelemetryChart option={heapChart} />
                          ) : (
                            <EmptyState
                              title="Sem dados de heap"
                              text="Não há amostras históricas de heap nesta janela."
                            />
                          )}
                        </div>
                      </div>

                      <div className="dashboard-panel">
                        <div className="dashboard-panel-header">
                          <div>
                            <div className="card-title">PSRAM</div>
                            <div className="card-subtitle">
                              Livre, piso e maior bloco.
                            </div>
                          </div>
                        </div>
                        <div className="chart-area chart-area-lg">
                          {hasPsramData ? (
                            <TelemetryChart option={psramChart} />
                          ) : (
                            <EmptyState
                              title="Sem dados de PSRAM"
                              text="Não há amostras históricas de PSRAM nesta janela."
                            />
                          )}
                        </div>
                      </div>

                      <div className="dashboard-panel">
                        <div className="dashboard-panel-header">
                          <div>
                            <div className="card-title">Rede e envio</div>
                            <div className="card-subtitle">
                              Tempo máximo de POST e RSSI.
                            </div>
                          </div>
                        </div>
                        <div className="chart-area chart-area-lg">
                          {hasNetworkData ? (
                            <TelemetryChart option={signalChart} />
                          ) : (
                            <EmptyState
                              title="Sem dados de rede"
                              text="Não há amostras históricas de sinal ou envio nesta janela."
                            />
                          )}
                        </div>
                      </div>

                      <div className="dashboard-panel">
                        <div className="dashboard-panel-header">
                          <div>
                            <div className="card-title">Presença PIR</div>
                            <div className="card-subtitle">
                              Detecções agrupadas em {pirBucketLabel}.
                            </div>
                          </div>
                        </div>
                        <div className="chart-area chart-area-lg">
                          {hasPirData ? (
                            <TelemetryChart option={pirChart} />
                          ) : (
                            <EmptyState
                              title="Sem dados PIR"
                              text="Não há eventos de presença PIR nesta janela."
                            />
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
          </div>
        )}
      </section>
    </section>
  );

  return (
    <>
      <PageMeta
        title="Mapa IoT | AutoPonto"
        description="Mapa público de dispositivos IoT AutoPonto."
      />
      {embedded ? (
        content
      ) : (
        <main className="public-page">
          <header className="public-topbar">
            <div className="public-topbar-inner">
              <Link to="/" className="public-brand-link">
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
