from typing import Any, List, Union
from io import IOBase, BytesIO
from bdsim.blocks.discrete import ZOH
import utime

import msgpack
import numpy as np
import micropython

from bdsim.components import Block, Clock, Plug, SinkBlock, SourceBlock, block, ClockedBlock
from bdsim.profiling import timed


# pivate helpers
_PKT_LEN_SIZE = 4


send_buffer = BytesIO(bytearray(128))

# @timed


@micropython.native
def _send_msgpack(transport: IOBase, obj: Any):
    if isinstance(obj, list):
        # we can't send ndarrays (yet). Convert them to a single list of numbers
        for idx, o in enumerate(obj):
            while isinstance(o, np.ndarray):
                assert len(o) == 0
                o = o[0]
            obj[idx] = o

    # toc("unwrapped")

    send_buffer.seek(_PKT_LEN_SIZE)
    msgpack._pack3(obj, send_buffer)

    # toc("encoded")

    data_len = send_buffer.tell() - _PKT_LEN_SIZE

    # toc("got len")
    l = data_len.to_bytes(_PKT_LEN_SIZE, 'big')

    # toc('cvt to bytes')
    send_buffer.seek(0)
    send_buffer.write(l)

    # toc("framed")

    # should be the only buffer allocation
    send_buffer.seek(0)
    transport.write(send_buffer.read(data_len + _PKT_LEN_SIZE))

    # toc('written')


@micropython.native
def _recv_msgpack(transport: IOBase) -> Any:
    return msgpack.loads(
        transport.read(
            int.from_bytes(transport.read(_PKT_LEN_SIZE), 'big')))

_emptylist = []

@block
class DataSender(SinkBlock, ClockedBlock):

    def __init__(self, receiver: IOBase, *inputs: Union[Block, Plug], nin: int, clock: Clock, **kwargs: Any):

        # multiple super classes fail silently in micropython - so can't do super()
        SinkBlock.__init__(self, nin=nin, nout=0, inputs=inputs, **kwargs)
        ClockedBlock.__init__(self, clock=clock)

        self._x0 = np.zeros(0)
        self.receiver = receiver
        self.type = 'datasender'
        self.ready = False

        # SYN -> server(receiver):SYN-ACK -> ACK (copy TCP scheme)
        _send_msgpack(receiver, {
            'version': '0.0.1',
            'role': 'sender'
        })

        syn_ack = _recv_msgpack(receiver)
        assert syn_ack['version'] == '0.0.1'

        _send_msgpack(receiver, {
            'version': '0.0.1',
            'role': 'sender'
        })

    # @timed
    @micropython.native
    def tick(self, dt: float):
        _send_msgpack(self.receiver, self.inputs)

    @micropython.native
    def output(self, t: float):
        return _emptylist


@block
class DataReceiver(SourceBlock, ZOH):
    # TODO: Should only work with bdsim-realtime

    def __init__(self, sender: IOBase, *, nout: int, clock: Clock, **kwargs: Any):
        # multiple super classes fail silently in micropython - so can't do super()
        ClockedBlock.__init__(self, clock=clock)
        SourceBlock.__init__(self, nin=0, nout=nout, **kwargs)

        self._x = [0] * nout
        self.ndstates = len(self._x0)
        self.sender = sender
        self.type = 'datareceiver'

        syn = _recv_msgpack(sender)
        assert syn['version'] == '0.0.1'

        _send_msgpack(sender, {
            'version': '0.0.1',
            'role': 'receiver'
        })

        ack = _recv_msgpack(sender)
        assert ack['version'] == '0.0.1'

    @micropython.native
    def tick(self, dt: float):
        # should be a list
        self._x = _recv_msgpack(self.sender)

    @micropython.native
    def output(self, t: float):
        return self._x


@block
class CSV(SinkBlock):

    def __init__(
        self,
        file: IOBase,
        *inputs: Union[Block, Plug],
        nin: int,
        time: bool = True,
        **kwargs: Any
    ):
        super().__init__(nin=nin, nout=0, inputs=inputs, **kwargs)
        self.file = file
        self.type = "csv"
        self.time = time

    def step(self):
        if self.time:
            self.file.write(str(self.bd.state.t))
            the_rest = self.inputs
        else:
            self.file.write(str(self.inputs[0]))
            the_rest = self.inputs[1:]

        for inp in the_rest:
            self.file.write(",{}".format(inp))

        self.file.write('\n')
