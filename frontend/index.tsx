import React from "react";
import { render } from "react-dom";

import { ReactGoldenLayout } from "@annotationhub/react-golden-layout";
import "@annotationhub/react-golden-layout/dist/css/goldenlayout-base.css";
import "@annotationhub/react-golden-layout/dist/css/themes/goldenlayout-dark-theme.css";
const { Row, Column, Content } = ReactGoldenLayout;

import VideoStream from "./VideoStream";
import ParamEditorDelegator from "./ParamEditor/Delegator";
import { useApi, Api } from "./api";
import "./style.scss";

function App() {
  const api = useApi();
  return !api ? (
    <p>Connecting to websocket at {Api.WS_URL}</p>
  ) : api instanceof Error ? (
    <p>Connection error: {api}</p>
  ) : (
    <NodeInterface api={api} />
  );
}

function NodePicker({ api }: { api: Api }) {
  const [availableNodeUrls] = api.availableNodeUrls.useState();

  return (
    <label style={{ margin: 20 }}>
      Connected:
      <select
        onInput={(e) =>
          api.setCurrentNode((e.target as HTMLSelectElement).value)
        }
      >
        {availableNodeUrls.map((url) => (
          <option value={url}>{url}</option>
        ))}
      </select>
    </label>
  );
}

export function NodeInterface({ api }: { api: Api }) {
  const [currentNode] = api.currentNode.useState();

  return (
    <div style={{ width: "100vw", height: "100vh" }}>
      <NodePicker api={api} />

      {currentNode ? (
        <ReactGoldenLayout>
          <Row>
            <Content title="Panel 1" width={20}>
              {currentNode.params.map((param) => (
                <ParamEditorDelegator param={param} />
              ))}
            </Content>

            <Column width={80}>
              {currentNode.videoStreamUrls.map((url) => (
                <Content title={`VideoStream ${url}`} key={url}>
                  <VideoStream url={url} />
                </Content>
              ))}
            </Column>
          </Row>
        </ReactGoldenLayout>
      ) : (
        <div>Not connnected</div>
      )}
    </div>
  );
}

render(<App />, document.body);
