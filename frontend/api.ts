import { AnyParam } from "./paramTypes";
import { useState, useEffect } from "react";
import { decode, encode } from "@msgpack/msgpack";

type Callback<T> = (state: T) => void;

// something neat I came up with
export class Observable<T> {
  state: T;
  callbacks: Callback<T>[];

  constructor(init: T, onChange: Callback<T> | null = null) {
    this.state = init;
    this.callbacks = onChange ? [onChange] : [];
  }

  // register with react lifecycle
  useState(): [T, (state: T) => void] {
    const [state, setState] = useState<T>(this.state);
    useEffect(() => {
      this.onChange(setState);
      return () => this.deRegister(setState);
    }, []);
    return [state, this.set.bind(this)];
  }

  onChange(cb: Callback<T>) {
    this.callbacks.push(cb);
  }

  deRegister(cb: Callback<T>) {
    this.callbacks.splice(this.callbacks.indexOf(cb), 1);
  }

  set(state: T) {
    this.state = state;
    for (const cb of this.callbacks) {
      cb(state);
    }
  }
}

type AvailableNodesApiMsg = {
  available_nodes: string[];
};

type BdsimNodeDescApiMsg = {
  url: string;
  params: AnyParam[];
  video_streams: string[];
  signal_scopes: SignalScope[];
};

type ParamUpdateApiMsg = AnyParam[];

type SignalScopeApiMsg = [id: number, ...data: number[][]];

type ApiMsg =
  | AvailableNodesApiMsg
  | BdsimNodeDescApiMsg
  | ParamUpdateApiMsg
  | SignalScopeApiMsg;

type BDSimNode = {
  url: string;

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

  // millliseconds of data to retain and display -
  // prevents memory usage from growing indefinitely
  keepLastMS: number;
};
export class Api {
  ws: WebSocket;
  availableNodeUrls: Observable<string[]>;
  currentNode: Observable<BDSimNode | null>;

  // can't just use "/ws". WebSocket constructor won't accept it.
  static WS_URL = "ws://" + document.domain + ":" + location.port + "/ws";

  constructor(ws: WebSocket) {
    this.ws = ws;
    this.availableNodeUrls = new Observable(["None"]);
    this.currentNode = new Observable(null);

    ws.onmessage = async ({ data }: { data: Blob }) =>
      this.onMsg(decode(await data.arrayBuffer()) as ApiMsg);
  }

  private onMsg(msg: ApiMsg) {
    const raiseUnhandled = () => {
      console.error(`Unhandled Api message`, msg);
      throw new Error(`Unhandled Api message ${msg}`);
    };

    if (Array.isArray(msg)) {
      if (typeof msg[0] === "number") {
        const [idx, ...data] = msg as SignalScopeApiMsg;
      } else if ("name" in msg[0]) {
        msg as ParamUpdateApiMsg;
      } else {
        raiseUnhandled();
      }
    } else if ("available_nodes" in msg) {
      const nodes = msg.available_nodes;
      if (nodes.length == 0) {
        this.availableNodeUrls.set(["None"]);
        if (this.currentNode.state !== null) {
          window.alert(`${this.currentNode.state.url} disconnected`);
          this.currentNode.set(null);
        }
      } else {
        this.availableNodeUrls.set(nodes);
        this.setCurrentNode(nodes[0]);
      }
    } else if ("params" in msg) {
      let id2param: BDSimNode["id2param"] = {};
      const params = msg.params.map(function wrapObservable(param: AnyParam) {
        const observableParam = new Observable(param);
        id2param[param.id] = observableParam;
        if ("params" in param) {
          // subParams aren't wrapped in observables in their serialized form -
          // do so recursively.
          for (const [attr, subParam] of Object.entries(param.params)) {
            param.params[attr] = wrapObservable(
              (subParam as unknown) as AnyParam
            );
          }
        }

        return observableParam;
      });

      this.currentNode.set({
        url: msg.url,
        videoStreamUrls: msg.video_streams,
        id2param,
        params,

        signalScopes: msg.signal_scopes.map((scope: SignalScope) => ({
          ...scope,
          data: new Observable(Array(scope.n + 1).map(() => [])), // init empty data arrays
          keepLastMS: 60 * 1000, // keep a minute's worth of data - TODO: send this from scope block
        })),
      });
    } else {
      raiseUnhandled();
    }
  }

  private send(msg: any) {
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
