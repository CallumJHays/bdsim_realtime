import React, { useEffect, useRef, useState } from "react";
import uPlot from "uplot";
import "uplot/dist/uPlot.min.css";

import { SignalScope } from "./api";

export function SignalScopeChart({ scope }: { scope: SignalScope }) {
  // use the same modern matplotlib default colours
  const VEGA_CAT_10_COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
  ];

  const [data] = scope.data.useState();
  const containerRef = useRef<HTMLDivElement>();
  const chartRef = useRef<uPlot>();

  // update the chart
  useEffect(() => {
    const container = containerRef.current;
    if (chartRef.current) {
      chartRef.current.setData(data as any);
      //   console.log("setData", data);
    } else if (container && !chartRef.current) {
      chartRef.current = new uPlot(
        {
          width: 600,
          height: 400,
          series: [
            {
              label: "Time (secs since boot)",
            },
            ...scope.labels.map((label, i) => ({
              label,
              stroke: VEGA_CAT_10_COLORS[i % VEGA_CAT_10_COLORS.length],
            })),
          ],
          axes: [
            { stroke: "white", grid: { stroke: "white", width: 0.1 } },
            { stroke: "white", grid: { stroke: "white", width: 0.1 } },
          ],
          scales: {
            x: {
              time: false,
            },
          },
        },
        data as any, // uPlot.js types incorrect here
        container
      );

      new ResizeObserver(() => {
        const LEGEND_HEIGHT = 25;
        chartRef.current.setSize({
          width: container.parentElement.offsetWidth,
          height: container.parentElement.offsetHeight - LEGEND_HEIGHT,
        });
      }).observe(container.parentElement);
    }
  }, [containerRef, data]);

  return <div ref={containerRef} />;
}
