import React from "react";

import { ParamEditorProps } from "./Delegator";

export default function BoolParamEditor({
  param,
  onChange,
}: ParamEditorProps<boolean>) {
  return (
    <>
      <input
        type="checkbox"
        checked={param.val}
        onClick={(e: any) => {
          e.stopPropagation(); // disable event bubbling for checkboxes inside collapsibles
          onChange(e.target.checked);
        }}
      />
      {param.name}
    </>
  );
}
