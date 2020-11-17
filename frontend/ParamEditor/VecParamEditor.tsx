import React from "react";

import { VecParam } from "../paramTypes";
import Collapsible from "./Collapsible";
import { ParamEditorProps } from "./Delegator";
import NumParamEditor from "./NumParamEditor";

export default function VecParamEditor({
  param,
  onChange,
}: ParamEditorProps<number[], VecParam>) {
  const { name, val, min, max, log_scale, step } = param;

  return (
    <Collapsible title={name}>
      {val.map((scalar, idx) => (
        <NumParamEditor
          param={{
            name: "",
            id: null,
            val: scalar,
            min: min[idx],
            max: max[idx],
            log_scale,
            step,
          }}
          onChange={(scalar) => {
            param.val[idx] = scalar;
            onChange(param.val);
          }}
        />
      ))}
    </Collapsible>
  );
}
