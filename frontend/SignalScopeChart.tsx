import React, { useEffect, useRef, useState } from "react";
import uPlot from "uplot";
import "uplot/dist/uPlot.min.css";

import { SignalScope } from "./api";

export function SignalScopeChart({ scope }: { scope: SignalScope }) {
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
              label: "x",
            },
            {
              label: "y",
              stroke: "red",
            },
          ],
          axes: [
            { stroke: "white", grid: { stroke: "white", width: 0.1 } },
            { stroke: "white", grid: { stroke: "white", width: 0.1 } },
          ],
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
