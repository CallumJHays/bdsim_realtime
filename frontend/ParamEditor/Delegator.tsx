import React, { JSX } from "react";

import { Observable } from "../observable";
import { AnyParam, Param, NumParam, VecParam, ParamVal } from "../paramTypes";
import BoolParamEditor from "./BoolParamEditor";
import HyperParamEditor from "./HyperParamEditor";
import EnumParamEditor from "./EnumParamEditor";
import VecParamEditor from "./VecParamEditor";
import NumParamEditor from "./NumParamEditor";
import StringParamEditor from "./StringParamEditor";

// used by all param editors
export type ParamEditorProps<
  T extends ParamVal,
  P extends Param<T> = Param<T>
> = {
  param: P;
  onChange?: (val: T) => void; // only undefined for HyperParamEditor
};

export default function Delegator({
  param: observableParam,
  showLabel = true,
}: {
  param: Observable<AnyParam>;
  showLabel?: boolean;
}) {
  const [param, setParam] = observableParam.useState();

  const Editor: <T extends ParamVal>(
    props: ParamEditorProps<T>
  ) => JSX.Element = ("params" in param
    ? HyperParamEditor
    : "oneof" in param
    ? EnumParamEditor
    : "max" in param
    ? typeof param.val === "number"
      ? NumParamEditor
      : VecParamEditor
    : typeof param.val === "boolean"
    ? BoolParamEditor
    : typeof param.val === "string"
    ? StringParamEditor
    : null) as any;

  return (
    <div class="param-editor">
      <Editor
        param={showLabel ? param : { ...param, name: "" }}
        onChange={(val) => setParam({ ...param, val })}
      />
    </div>
  );
}
