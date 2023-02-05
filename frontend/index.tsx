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
import { SignalScopeChart } from "./SignalScopeChart";

function App() {
  const api = useApi();
  return !api ? (
    <p>Attempting to connect to to websocket server at {Api.WS_URL}</p>
  ) : api instanceof Error ? (
    <p>Connection error: {api}</p>
  ) : (
    <NodeInterface api={api} />
  );
}

function NodePicker({ api }: { api: Api }) {
  const [availableNodeIPs] = api.availableNodeIPs.useState();

  return (
    <label style={{ margin: 20 }}>
      Connected:
      <select
        onChange={(e) =>
          api.setCurrentNode((e.target as HTMLSelectElement).value)
        }
      >
        {availableNodeIPs.map((ip) => (
          <option key={ip} value={ip}>{ip}</option>
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
              height: "calc(100vh - 45px)",
            },
          }}
        >
          <Row>
            <Stack isClosable={false}>
              <Content title="Parameters" isClosable={false}>
                <div className="param-tuner">
                  {currentNode.params.map((param, idx) => (
                    <ParamEditorDelegator key={idx} param={param} />
                  ))}
                </div>
              </Content>
            </Stack>

            <Column isClosable={false}>
              <Stack isClosable={false}>
                {currentNode.videoStreamUrls.map((url) => (
                  <Content
                    title={url.split("/").pop()}
                    key={url}
                    isClosable={false}
                  >
                    <VideoStream url={url} />
                  </Content>
                ))}
              </Stack>
              <Stack isClosable={false}>
                {currentNode.signalScopes.map((scope) => (
                  <Content key={scope.name} title={scope.name} isClosable={false}>
                    <SignalScopeChart scope={scope} />
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

render(<App />, document.querySelector('#app'));
