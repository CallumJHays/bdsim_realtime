import React from "react";

import { ParamEditorProps } from "./Delegator";
import { EnumParam, ParamVal } from "../paramTypes";

export default function EnumParamEditor<T extends ParamVal>({
  param,
  onChange,
}: ParamEditorProps<T, EnumParam<T>>) {
  return (
    <label>
      {param.name}
      <select onChange={(e: any) => onChange(param.oneof[e.target.value])}>
        {param.oneof.map((val, idx) => (
          <option value={idx} selected={val === param.val}>
            {val.toString()}
          </option>
        ))}
      </select>
    </label>
  );
}
