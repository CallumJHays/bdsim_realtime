import { useState, useEffect } from "react";
import { decode, encode } from "@msgpack/msgpack";

import { AnyParam } from "./paramTypes";
import { Observable } from "./observable";

type AvailableNodesApiMsg = {
  available_nodes: string[];
};

type BdsimNodeDescApiMsg = {
  start_time: number; // ms since epoch
  ip: string;
  params: AnyParam[];
  video_streams: string[];
  signal_scopes: SignalScope[];
};

type ParamUpdateApiMsg = Partial<AnyParam>[];

type SignalScopeApiMsg = [
  id: number,
  ms_since_start: number[],
  ...data: number[]
];

type ApiMsg =
  | AvailableNodesApiMsg
  | BdsimNodeDescApiMsg
  | ParamUpdateApiMsg
  | SignalScopeApiMsg;

type BDSimNode = {
  startTime: number;
  ip: string;

  // lists the params top-level heirarchy (no subParams) in its display order
  params: Observable<AnyParam>[];

  // maps param id to its param (same one as in the list above)
  // so that api updates can reference the correct one. Includes subParams
  id2param: { [id: number]: Observable<AnyParam> };

  videoStreamUrls: string[];
  signalScopes: SignalScope[];
};

export type SignalScope = {
  name: string;
  n: number;
  styles: string | {} | null;
  labels: string[] | null;
  data: Observable<number[][]>;

  // seconds of data to retain and display -
  // prevents memory usage from growing indefinitely
  keepLastSecs: number;
};
export class Api {
  ws: WebSocket;
  availableNodeIPs: Observable<string[]>;
  currentNode: Observable<BDSimNode | null>;

  // can't just use "/ws". WebSocket constructor won't accept it.
  static WS_URL = "ws://" + document.domain + ":" + location.port + "/ws";
  // static WS_URL = "ws://localhost:8080/ws";

  constructor(ws: WebSocket) {
    this.ws = ws;
    this.availableNodeIPs = new Observable(["None Connected"]);
    this.currentNode = new Observable(null);

    ws.onmessage = async ({ data }: { data: Blob }) => {
      const apiMsg = await data.arrayBuffer();
      this.onMsg(decode(apiMsg) as ApiMsg);
    };
  }

  private onMsg(msg: ApiMsg) {
    const raiseUnhandled = () => {
      console.error(`Unhandled Api message`, msg);
      throw new Error(`Unhandled Api message ${msg}`);
    };

    if (Array.isArray(msg)) {
      if (typeof msg[0] === "number") {
        // signal data update
        const [idx, ...newData] = msg as SignalScopeApiMsg;
        const scope = this.currentNode.state.signalScopes[idx];

        // append the data
        const updatedData = scope.data.state.map((series, serIdx) =>
          series.concat(newData[serIdx])
        );

        // only keep scope.keepLastSecs worth of data
        const [time] = updatedData;
        const cutoffTime = time[time.length - 1] - scope.keepLastSecs;
        const cutoffIdx = time.findIndex((t) => t >= cutoffTime);
        // console.log({ cutoffIdx, cutoffTime, time });

        if (cutoffIdx > 0) {
          for (const series of updatedData) {
            series.splice(0, cutoffIdx);
          }
        }

        // update the observable{
        scope.data.set(updatedData);
      } else if ("name" in msg[0]) {
        // parameter change from backend
        for (const paramUpdate of msg as ParamUpdateApiMsg) {
          const param = this.currentNode.state.id2param[paramUpdate.id];
          param.set({ ...param.state, ...paramUpdate });
        }
      } else {
        raiseUnhandled();
      }
    } else if ("available_nodes" in msg) {
      // node connected / disconnected event (or connected for first time)
      const nodes = msg.available_nodes;
      if (nodes.length == 0) {
        this.availableNodeIPs.set(["None Connected"]);
        if (this.currentNode.state !== null) {
          window.alert(`${this.currentNode.state.ip} disconnected`);
          this.currentNode.set(null);
        }
      } else {
        this.availableNodeIPs.set(nodes);
        this.setCurrentNode(nodes[0]);
      }
    } else if ("params" in msg) {
      // on-connect node description
      let id2param: BDSimNode["id2param"] = {};
      const wrapObservable = (param: AnyParam) => {
        const observableParam = new Observable(param, (p) => {
          this.send([p.id, p.val]);
        });
        id2param[param.id] = observableParam;
        if ("params" in param) {
          // subParams aren't wrapped in observables in their serialized form -
          // do so recursively.
          for (const [attr, subParam] of Object.entries(param.params)) {
            param.params[attr] = wrapObservable(
              subParam as unknown as AnyParam
            );
          }
        }

        return observableParam;
      };
      const params = msg.params.map(wrapObservable);

      console.log({ msg });

      this.currentNode.set({
        startTime: msg.start_time,
        ip: msg.ip,
        videoStreamUrls: msg.video_streams,
        id2param,
        params,

        signalScopes: msg.signal_scopes.map((scope: SignalScope) => ({
          ...scope,
          data: new Observable(Array(scope.n + 1).fill([])), // init empty data arrays
          keepLastSecs: 5, // keep a minute's worth of data - TODO: send this from scope block
        })),
      });
    } else {
      raiseUnhandled();
    }
  }

  private send(msg: any) {
    console.log("sending", { msg, readyState: this.ws.readyState });
    this.ws.send(encode(msg));
  }

  setCurrentNode(nodeUrl: string) {
    this.send({ chosenNode: nodeUrl });
  }
}

export function useApi() {
  const [api, setApi] = useState<Api | Error | null>(null);

  useEffect(() => {
    try {
      const ws = new WebSocket(Api.WS_URL);
      ws.onopen = () => setApi(new Api(ws));
      ws.onclose = () => setApi(null);
      return ws.close; // effect cleanup handler
    } catch (e) {
      setApi(e); // set the connection error to show users
    }
  }, []);

  return api;
}
