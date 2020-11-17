import * as React from "react";

export default function VideoStream({ url }: { url: string }) {
  return <img class="stream-viewer" src={url} />;
}
