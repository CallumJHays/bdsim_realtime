import asyncio
from asyncio import StreamReader, StreamWriter
import os
import websockets
import json
from collections import namedtuple
import msgpack
from sanic import Sanic, response
from pathlib import Path
import argparse
import pdb

HERE = Path(__file__).parent

app = Sanic(__name__)


class RemoteBDSimNode:
    def __init__(self, reader, writer, ws_subs, param_defs):
        self.reader = reader
        self.writer = writer
        self.ws_subs = ws_subs
        self.param_defs = param_defs


tcp_clients = {}  # { RemoteBDSimNode: peername }
ws_clients = {}  # { websocket.send: RemoteBDSimNode }

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
async def ws(req, ws):
    chosen_node = None
    print("got ws client", ws)
    send = ws.send
    ws_clients[send] = None

    try:
        # let client know which nodes are available
        await send(available_nodes_message())
        print("sent available nodes")

        while True:
            print('waiting for ws message')
            new_msg = await ws.recv()
            print("got ws message", new_msg)
            try:
                # this should happen first, can messages shouldn't tranceive until so
                jason = json.loads(new_msg)
                print('got json', jason)
                chosen_node_peername = jason["chosenNode"]

                old_chosen_node = chosen_node
                if chosen_node_peername == "None":
                    chosen_node = None
                else:
                    chosen_node = next(
                        client for peername, client in tcp_clients.items()
                        if peername == chosen_node_peername)

                # only reconnect if it's changed
                if chosen_node != old_chosen_node:
                    # disconnect and reconnect to newly chosen node
                    ws_disconnect(send)
                    ws_clients[send] = chosen_node
                    if chosen_node:
                        ws_clients[send].ws_subs.add(send)

                        # send the param definitions
                        await send(msgpack.packb(chosen_node.param_defs))

            except (UnicodeDecodeError, json.JSONDecodeError):
                print("sending to ", chosen_node_peername)
                chosen_node.writer.write(new_msg)
                await chosen_node.writer.drain()
                print("sent", new_msg)

    except asyncio.CancelledError:
        print('got error')
        ws_disconnect(send)


@app.route('/')
async def index(req):
    return await response.file('dist/index.html')


app.static('/', 'dist')


def ws_disconnect(ws_send):
    if ws_clients[ws_send]:
        print('disconnecting', ws_send)
        pdb.set_trace()
        ws_clients[ws_send].ws_subs.remove(ws_send)
        del ws_clients[ws_send]


def available_nodes_message():
    return json.dumps({"availableNodes": list(tcp_clients.keys())})


async def broadcast_available_nodes():
    await send_all_ws(ws_clients, available_nodes_message())
    print("broadcasting available nodes")


async def send_all_ws(clients, message):
    print('send_all_ws', clients, message)
    if any(clients):
        websockets = list(clients)
        results = await asyncio.gather(
            *[send(message) for send in websockets],
            return_exceptions=True,
        )

        # remove disconnected clients
        for idx, res in enumerate(results):
            if isinstance(res, Exception):
                ws_disconnect(websockets[idx])


async def handle_tcp_conn(reader: StreamReader, writer: StreamWriter):
    [ip, port] = writer.get_extra_info("peername")
    print('got new tcp client connection from', ip, port)
    peername = f"{ip}:{port}"
    ws_subs = set()
    msgs = msgpack.Unpacker()

    msgs.feed(await reader.read(4096))
    param_defs = next(msgs)  # first message is always the param definition
    tcp_clients[peername] = RemoteBDSimNode(reader, writer, ws_subs,
                                            param_defs)

    await broadcast_available_nodes()

    try:
        while True:
            msgs.feed(await reader.read(1024))
            for msg in msgs:
                print('got tcp message', msg)
                await send_all_ws(ws_subs, msgpack.packb(msg))

    except asyncio.CancelledError:
        print(f"Remote {peername} closing connection.")
        writer.close()
        await writer.wait_closed()
    except asyncio.IncompleteReadError:
        print(f"Remote {peername} disconnected")
    finally:
        await broadcast_available_nodes()
        print(f"Remote {peername} closed")
        del tcp_clients[peername]


async def tcp_server(*args, **kwargs):
    server = await asyncio.start_server(handle_tcp_conn, *args, **kwargs)
    async with server:
        await server.serve_forever()


print(f"TCP server: {args.host or args.tcp_host}:{args.tcp_port}")
app.add_task(tcp_server(host=args.host or args.tcp_host, port=args.tcp_port))

if __name__ == "__main__":
    # TODO: omit debug
    app.run(host=args.host or args.app_host, port=args.app_port)
