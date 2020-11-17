import React, { JSX, useState } from "react";

export default function Collapsible({
  title,
  children,
}: {
  title: string;
} & JSX.ElementChildrenAttribute) {
  const [active, setActive] = useState(false);

  return (
    <>
      <button
        class={"collapsible-button" + (active ? " active" : "")}
        onClick={() => setActive(!active)}
      >
        {title}
      </button>
      <div class={"collapsible-panel" + (active ? " active" : "")}>
        {children}
      </div>
    </>
  );
}
