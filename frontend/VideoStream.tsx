import * as React from "react";

export default function VideoStream({ url }: { url: string }) {
  return <img className="stream-viewer" src={url} />;
}
