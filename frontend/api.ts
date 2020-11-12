import { AnyParam } from "./paramTypes";
import { useState, useEffect } from "react";
import { decode, encode } from "@msgpack/msgpack";

// poor mans rxjs with hooks
export class Observable<T> {
  state: T;
  callbacks: ((state: T) => void)[];

  constructor(init: T) {
    this.state = init;
    this.callbacks = [];
  }

  // play nice with react
  useState(): [T, (state: T) => void] {
    const [state, setState] = useState<T>(this.state);
    useEffect(() => {
      this.callbacks.push(setState);
      return () => this.callbacks.filter((cb) => cb != setState);
    });
    return [state, this.set];
  }

  set(state: T) {
    this.state = state;
    for (const cb of this.callbacks) {
      cb(state);
    }
  }
}

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
      this.onMsg(decode(await data.arrayBuffer()));
  }

  private onMsg(msg: any) {
    console.log("recieved api message", msg);
    if ("availableNodes" in msg) {
      const nodes = msg["availableNodes"];
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
      this.currentNode.set({
        url: msg["url"],
        params: msg["params"].map((p: AnyParam) => new Observable(p)),
        videoStreamUrls: msg["video_streams"],
      });
    } else {
      throw new Error(`Unhandled Api message ${msg}`);
    }
  }

  private send(msg: any) {
    this.ws.send(encode(msg));
  }

  setCurrentNode(nodeUrl: string) {
    this.send({ chosenNode: nodeUrl });
  }
}

type BDSimNode = {
  url: string;
  params: Observable<AnyParam>[];
  videoStreamUrls: string[];
};

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
