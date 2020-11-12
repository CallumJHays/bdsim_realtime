import { NumParam } from "frontend/paramTypes";
import React from "react";

import { ParamEditorProps } from "./Delegator";

export default function NumParamEditor({
  param,
  onChange,
}: ParamEditorProps<boolean, NumParam>) {
  return (
    <input
      type="checkbox"
      checked={param.val}
      onChange={(e: any) => onChange(e.target.checked)}
    />
  );
}
