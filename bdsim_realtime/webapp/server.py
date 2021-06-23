import asyncio
from asyncio import StreamReader, StreamWriter
import msgpack
from sanic import Sanic, response
from sanic.websocket import WebSocketCommonProtocol as WebSocket
from pathlib import Path
import argparse
from typing import Set

CLIENT_PATH = str(Path(__file__).parent / 'client')


class RemoteBDSimNode:
    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 ws_subs: Set[WebSocket], node_def):
        self.reader = reader
        self.writer = writer
        self.ws_subs = ws_subs
        self.node_def = node_def

    # def get_node_def(self):
    #     self.writer.write()

def cli():
    app = Sanic(__name__)

    tcp_clients = {}  # { url: RemoteBDSimNode }
    ws_clients = {}  # { WebSocket: RemoteBDSimNode}

    parser = argparse.ArgumentParser()
    parser.add_argument('--host',
                        type=int,
                        default=None,
                        help='sets both tcp-host and app-host at once')
    parser.add_argument('--tcp-host', type=str, default='localhost')
    parser.add_argument('--tcp-port', type=int, default=31337)
    parser.add_argument('--app-host', type=str, default='localhost')
    parser.add_argument('--app-port', type=int, default=8080)
    args = parser.parse_args()


    @app.websocket('/ws')
    async def ws(req, ws: WebSocket):
        chosen_node = None
        print("got ws client", ws)
        ws_clients[ws] = None

        try:
            # let client know which nodes are available
            await send_msg(available_nodes_message(), ws)
            print("sent available nodes")

            while True:
                print('waiting for ws message')
                msg, raw = await recv_msg(ws)
                print("got ws message", msg)

                # if this is just the client choosing a new node
                if isinstance(msg, dict) and 'chosenNode' in msg:
                    chosen_node_peername = msg["chosenNode"]

                    old_chosen_node = chosen_node
                    if chosen_node_peername == "None":
                        chosen_node = None
                    else:
                        chosen_node = tcp_clients[chosen_node_peername]

                    # only reconnect if it's changed
                    if chosen_node != old_chosen_node:
                        # disconnect and reconnect to newly chosen node
                        ws_disconnect(ws)
                        ws_clients[ws] = chosen_node
                        if chosen_node:
                            ws_clients[ws].ws_subs.add(ws)

                            # send the current param definitions
                            # TODO: query the node for these param definitions on connect
                            await send_msg(chosen_node.node_def, ws)

                else:  # send it directly to the node
                    # TODO: update these chosen_node.node_def according to client-node comms
                    chosen_node.writer.write(raw)
                    await chosen_node.writer.drain()
                    print('proxied', msg, 'to chosen node', chosen_node)

        except asyncio.CancelledError:
            print('websocket', ws, 'disconnected')
            ws_disconnect(ws)


    async def recv_msg(ws: WebSocket):
        raw = await ws.recv()
        return msgpack.unpackb(raw), raw


    async def send_msg(msg, ws: WebSocket):
        return await ws.send(msgpack.packb(msg))


    @app.route('/')
    async def index(req):
        return await response.file(CLIENT_PATH + '/index.html')


    app.static('/', CLIENT_PATH)


    def ws_disconnect(ws: WebSocket):
        if ws_clients[ws]:
            print('disconnecting', ws)
            ws_clients[ws].ws_subs.remove(ws)
            del ws_clients[ws]


    def available_nodes_message():
        return {"available_nodes": list(tcp_clients.keys())}


    async def broadcast_available_nodes():
        await send_all_ws(ws_clients, available_nodes_message())
        print("broadcasting available nodes")


    async def send_all_ws(clients, message):
        # print('send_all_ws', clients, message)
        if any(clients):
            websockets = list(clients)
            results = await asyncio.gather(
                *[ws.send(message) for ws in websockets],
                return_exceptions=True,
            )

            # remove disconnected clients
            for idx, res in enumerate(results):
                if isinstance(res, Exception):
                    ws_disconnect(websockets[idx])


    async def handle_tcp_conn(reader: StreamReader, writer: StreamWriter):
        [ip, port] = writer.get_extra_info("peername")
        print('got new tcp client connection from', ip, port)
        peername = ip + ":" + str(port)
        ws_subs = set()
        msgs = msgpack.Unpacker()

        msgs.feed(await reader.read(4096))
        node_def = next(msgs)  # first message is always the param definition
        print('node_def', node_def)
        tcp_clients[peername] = RemoteBDSimNode(reader, writer, ws_subs, node_def)

        await broadcast_available_nodes()

        try:
            while True:
                msgs.feed(await reader.read(1024))
                for msg in msgs:
                    # print('got tcp message', msg)
                    await send_all_ws(ws_subs, msgpack.packb(msg))

        # surely this is overkill. copied from example
        except asyncio.CancelledError:
            print("Remote " + peername + " closing connection.")
            writer.close()
            await writer.wait_closed()
        except asyncio.IncompleteReadError:
            print("Remote " + peername + " closing connection.")
        finally:
            await broadcast_available_nodes()
            print("Remote " + peername + " closing connection.")
            del tcp_clients[peername]


    async def tcp_server(*args, **kwargs):
        server = await asyncio.start_server(handle_tcp_conn, *args, **kwargs)
        async with server:
            await server.serve_forever()

    app.add_task(tcp_server(host=args.host or args.tcp_host, port=args.tcp_port))
    print("TCP server: " + str(args.host or args.tcp_host) + ":" +
        str(args.tcp_port))  
    # def run():
    app.run(host=args.host or args.app_host, port=args.app_port)



if __name__ == "__main__":
   cli()