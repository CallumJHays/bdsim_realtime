import React, { JSX, useState } from "react";

export default function Collapsible({
  title,
  children,
  disabled = false,
  activeState: [active, setActive] = useState(false),
}: {
  title: string | JSX.Element;
  disabled?: boolean;
  activeState?: [boolean, React.StateUpdater<boolean>];
} & JSX.ElementChildrenAttribute) {
  return (
    <>
      <button
        class={
          "collapsible-button" +
          (active ? " active" : "") +
          (disabled ? " disabled" : "")
        }
        onClick={() => {
          console.log("clicked2");
          setActive(!active);
        }}
        disabled={disabled}
      >
        {title}
      </button>
      <div class={"collapsible-panel" + (active ? " active" : "")}>
        {children}
      </div>
    </>
  );
}
