"Script for easily setting up a data-file recording server via command-line"

import os
import socket

from bdsim import BDSim
import bdsim_realtime

DATARECEIVER_ADDR = "192.168.0.11", 6404

serversocket = socket.socket()
# tell OS to recapture the socket
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(DATARECEIVER_ADDR)
serversocket.listen(1) # listen for only 1 connection

print("Awaiting TCP connection on", DATARECEIVER_ADDR)
clientsocket, address = serversocket.accept()
print("Client CONNECTED from", address)

bd = BDSim().blockdiagram()

fileno = 0
while True:
    filepath = "bdsim-dataout-%d.csv" % fileno
    if not os.path.exists(filepath):
        break
    fileno += 1

CHANNELS = 6

recv = bd.DATARECEIVER(
    clientsocket.makefile('rwb'),
    nout=CHANNELS,
    # run at a much higher hz but block
    clock=bd.clock(200, unit="Hz"))

bd.CSV(open(filepath, 'w'), recv[0:CHANNELS], nin=CHANNELS, time=False)

bdsim_realtime.run(bd)