import React, { JSX } from "react";

import { Observable } from "../api";
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
  onChange: (val: T) => void;
};

export default function Delegator({
  param: observableParam,
}: {
  param: Observable<AnyParam>;
}) {
  const [param] = observableParam.useState();
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
    <Editor
      param={param}
      onChange={(v) => {
        param.val = v;
        observableParam.set(param);
      }}
    />
  );
}
