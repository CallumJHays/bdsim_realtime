import asyncio
from asyncio import StreamReader, StreamWriter
import msgpack
from sanic import Sanic, response, Websocket
from pathlib import Path
import argparse
from typing import Set, Optional
import uvloop


app = Sanic('bdsim-webapp-server')

CLIENT_PATH = str((Path(__file__).parent / './frontend_dist').resolve())

print(CLIENT_PATH)

class RemoteBDSimNode:
    def __init__(self, reader: StreamReader, writer: StreamWriter,
                 ws_subs: Set[Websocket], node_def):
        self.reader = reader
        self.writer = writer
        self.ws_subs = ws_subs
        self.node_def = node_def

    # def get_node_def(self):
    #     self.writer.write()

tcp_clients = {}  # { url: RemoteBDSimNode }
ws_clients = {}  # { Websocket: RemoteBDSimNode}



@app.websocket('/ws')
async def ws(req, ws: Websocket):
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
        print('Websocket', ws, 'disconnected')
        ws_disconnect(ws)


async def recv_msg(ws: Websocket):
    raw = await ws.recv()
    return msgpack.unpackb(raw), raw


async def send_msg(msg, ws: Websocket):
    return await ws.send(msgpack.packb(msg))


@app.route('/')
async def index(req):
    return await response.file(CLIENT_PATH + '/index.html')


app.static('/', CLIENT_PATH)


def ws_disconnect(ws: Websocket):
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
        Websockets = list(clients)
        results = await asyncio.gather(
            *[ws.send(message) for ws in Websockets],
            return_exceptions=True,
        )

        # remove disconnected clients
        for idx, res in enumerate(results):
            if isinstance(res, Exception):
                ws_disconnect(Websockets[idx])


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


async def tcp_server(host: str, port: int):
    server = await asyncio.start_server(
        handle_tcp_conn,
        host=host,
        port=port
    )

    async with server:
        print("TCP server: " + str(host) + ":" + str(port))
        await server.serve_forever()


def run_forever(
    host: str = 'localhost',
    tcp_port: int = 31337,
    app_port: int = 8080
):

    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)

    # big f-around to get this working in newest version of sanic:
    ws_server = loop.run_until_complete(
        app.create_server(host=host, port=app_port, return_asyncio_server=True)
    )
    loop.run_until_complete(ws_server.startup())
    # loop.run_until_complete(ws_server.start_serving())

    asyncio.ensure_future(ws_server.serve_forever())
    asyncio.ensure_future(tcp_server(host, tcp_port))
    loop.run_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--tcp-comms-port', type=int, default=31337)
    parser.add_argument('--webapp-port', type=int, default=8080)
    args = parser.parse_args()

    run_forever(
        args.host,
        args.tcp_comms_port,
        args.webapp_port
    )