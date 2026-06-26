import { useEffect, useRef } from "react";
import { BarChart, LineChart, ScatterChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TooltipComponent,
  DataZoomComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import type { EChartsOption } from "echarts";

type EChartProps = {
  option: EChartsOption;
  className?: string;
};

echarts.use([
  CanvasRenderer,
  BarChart,
  GridComponent,
  LegendComponent,
  LineChart,
  MarkLineComponent,
  ScatterChart,
  DataZoomComponent,
  TooltipComponent,
]);

export function EChart({ option, className }: EChartProps) {
  const elementRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!elementRef.current) return undefined;
    const chart = echarts.init(elementRef.current);
    const resizeObserver = new ResizeObserver(() => chart.resize());

    chart.setOption(option, true);
    resizeObserver.observe(elementRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.dispose();
    };
  }, []);

  useEffect(() => {
    const chart = elementRef.current
      ? echarts.getInstanceByDom(elementRef.current)
      : null;
    chart?.setOption(option, true);
  }, [option]);

  return <div ref={elementRef} className={className || "echart"} />;
}
