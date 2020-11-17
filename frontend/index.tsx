import React from "react";
import { render } from "react-dom";

import { ReactGoldenLayout } from "@annotationhub/react-golden-layout";
import "@annotationhub/react-golden-layout/dist/css/goldenlayout-base.css";
import "@annotationhub/react-golden-layout/dist/css/themes/goldenlayout-dark-theme.css";
const { Row, Column, Content, Stack } = ReactGoldenLayout;

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
        onChange={(e) =>
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
    <div>
      <NodePicker api={api} />

      {currentNode ? (
        <ReactGoldenLayout
          htmlAttrs={{
            style: {
              height: "calc(100vh - 40px)",
            },
          }}
        >
          <Row>
            <Stack width={40} isClosable={false}>
              <Content title="Parameters" isClosable={false}>
                <div class="param-tuner">
                  {currentNode.params.map((param) => (
                    <ParamEditorDelegator param={param} />
                  ))}
                </div>
              </Content>
            </Stack>

            <Column>
              <Stack isClosable={false}>
                {currentNode.videoStreamUrls.map((url) => (
                  <Content
                    title={`VideoStream ${url}`}
                    key={url}
                    isClosable={false}
                  >
                    <VideoStream url={url} />
                  </Content>
                ))}
              </Stack>
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
