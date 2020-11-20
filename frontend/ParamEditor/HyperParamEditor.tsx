import React, { JSX, useState } from "react";

import ParamEditorDelegator, { ParamEditorProps } from "./Delegator";
import { HyperParam, Param } from "../paramTypes";
import Collapsible from "./Collapsible";
import BoolParamEditor from "./BoolParamEditor";
import { Observable } from "frontend/api";

export default function HyperParamEditor({
  param,
  collapsible = true,
}: ParamEditorProps<null, HyperParam> & { collapsible?: boolean }) {
  // // if its an Optional HyperParam explicitly, inline the underlying value (if it's shown)
  const isOptional =
    "enabled" in param.params && "enabled_value" in param.params;
  if (isOptional) {
    const { enabled: enabledP, enabled_value: enabledValP } = param.params;

    // assume that this parameter will always remain an optional parameter -
    // and that this branch will always be executed if it ever executes
    const [enabled, setEnabled] = (enabledP as Observable<
      Param<boolean>
    >).useState();
    const [active, setActive] = useState(false);

    const wrapCollapsible = (child: JSX.Element) => (
      <Collapsible
        activeState={[active, setActive]}
        title={
          <BoolParamEditor
            param={{ ...enabled, name: param.name }}
            onChange={(val) => {
              setEnabled({ ...enabled, val });

              // open the collapsible if we enable it while it's closed
              // and vice-versa
              if (val !== active) {
                setActive(val);
              }
            }}
          />
        }
        disabled={!enabled.val}
      >
        {child}
      </Collapsible>
    );

    // same goes for this as above - if the enabled_value is a hyper param - using
    // hooks inside the conditional here makes the assumption that it always will be.
    const isHyperParam = "params" in enabledValP.state;
    if (isHyperParam) {
      const [subHyperParam] = (enabledValP as Observable<
        HyperParam
      >).useState();
      return wrapCollapsible(
        <HyperParamEditor param={subHyperParam} collapsible={false} />
      );
    } else {
      return wrapCollapsible(
        "enabled_value" in param ? null : (
          <ParamEditorDelegator param={enabledValP} showLabel={false} />
        )
      );
    }
  } else {
    let editors = [];
    for (const [attr, subParam] of Object.entries(param.params)) {
      if (!param.hidden.includes(attr)) {
        editors.push(<ParamEditorDelegator param={subParam} />);
      }
    }

    return collapsible ? (
      <Collapsible title={param.name}>{editors}</Collapsible>
    ) : (
      <>{editors}</>
    );
  }
}
