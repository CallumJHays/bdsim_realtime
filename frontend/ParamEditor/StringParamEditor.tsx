import React from "react";

import { ParamEditorProps } from "./Delegator";

export default function BoolParamEditor({
  param,
  onChange,
}: ParamEditorProps<string>) {
  return (
    <input value={param.val} onChange={(e: any) => onChange(e.target.value)} />
  );
}
