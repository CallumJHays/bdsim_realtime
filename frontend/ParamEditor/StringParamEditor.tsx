import React from "react";

import { ParamEditorProps } from "./Delegator";

export default function BoolParamEditor({
  param,
  onChange,
}: ParamEditorProps<string>) {
  return (
    <input
      type="checkbox"
      checked={param.val}
      onChange={(e: any) => onChange(e.target.checked)}
    />
  );
}
