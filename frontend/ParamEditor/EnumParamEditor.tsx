import React from "react";

import { ParamEditorProps } from "./Delegator";
import { EnumParam, ParamVal } from "../paramTypes";

export default function EnumParamEditor<T extends ParamVal>({
  param,
  onChange,
}: ParamEditorProps<T, EnumParam<T>>) {
  return (
    <select>
      {param.oneof.map((val) => (
        <option>{val}</option>
      ))}
    </select>
  );
}
