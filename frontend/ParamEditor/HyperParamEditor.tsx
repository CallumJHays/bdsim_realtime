import React, { useState } from "react";

import ParamEditorDelegator, { ParamEditorProps } from "./Delegator";
import { HyperParam } from "../paramTypes";
import Collapsible from "./Collapsible";

export default function HyperParamEditor({
  param,
  collapsible = true,
}: ParamEditorProps<null, HyperParam> & { collapsible: boolean }) {
  const [active, setActive] = useState(false);
  const subParams = Object.entries(param.params)
    .filter(([attr]) => !param.hidden.includes(attr))
    .map(([_, observableParam]) => observableParam);

  // let flattenedParamStates;
  // // if its an Optional HyperParam explicitly, inline the underlying value (if it's shown)
  // const isOptional = // TODO: The order of these may not be guaranteed as they are extracted from an object
  //   subParamStates.length == 2 &&
  //   subParamStates[0][1][0].name == ".enabled" &&
  //   subParamStates[1][1][0].name === ".enabled_value";
  // if (isOptional) {
  //   const enabledState = subParamStates[0][1];
  //   const valueState = subParamStates[1][1];
  //   const isHyperParam = "params" in valueState[0];
  //   if (isHyperParam) {
  //     const hyperParam = valueState[0] as HyperParam;
  //     flattenedParamStates = [enabledState, hyperParam.params];
  //   } else {
  //     flattenedParamStates = [
  //       subParamStates[0],
  //       { ...subParamStates[1], name: "" },
  //     ];
  //   }
  // }

  const editors = subParams.map((param) => (
    <ParamEditorDelegator param={param} />
  ));

  return collapsible ? (
    <Collapsible title={param.name}>{editors}</Collapsible>
  ) : (
    editors
  );
}
