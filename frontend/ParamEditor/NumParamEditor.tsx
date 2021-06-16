import { NumParam } from "frontend/paramTypes";
import React, { useRef, useEffect } from "react";
import * as d3 from "d3";
import { sliderBottom } from "d3-simple-slider";

import { ParamEditorProps } from "./Delegator";

function formatNum(val: number) {
  const valStr = val.toString();
  const valAbs = Math.abs(val);
  // TODO: relate this behaviour to min and max somehow
  return valAbs > 0.001 && valAbs < 10000
    ? valStr.slice(0, 6)
    : valStr.length > 6
    ? d3.format(".2")(val)
    : valStr;
}

export default function NumParamEditor({
  param,
  onChange,
}: ParamEditorProps<number, NumParam>) {
  const { val, min, max, log_scale, step } = param;

  const sliderContainer = useRef<SVGGElement>();
  useEffect(() => {
    if (sliderContainer) {
      // TODO: replace this and d3 dependency with custom implementation.
      d3.select(sliderContainer.current).call(
        sliderBottom((log_scale ? d3.scaleLog : d3.scaleLinear)([min, max]))
          // @ts-ignore
          .default(val) // @types/d3-simple-slider missing this, max and default - HOW!?
          .min(min)
          .max(max)
          .ticks(4)
          .default(val)
          .step(step)
          .width(200)
          .on("onchange", onChange)
      );
    }
  }, [sliderContainer]);

  return (
    <>
      <div>{param.name}</div>
      <div class="slider-wrapper">
        <svg class="slider" width={230} height={47}>
          <g transform="translate(12, 6)" ref={sliderContainer} />
        </svg>
        <label class="slider-value">{formatNum(val)}</label>
      </div>
    </>
  );
}
