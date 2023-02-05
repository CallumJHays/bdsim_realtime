
import numpy as np
from bdsim.components import FunctionBlock

from bdsim_realtime.tuning.tunable_block import TunableBlock



class Tunable_Gain(FunctionBlock, TunableBlock):

    type = "gain"

    nin = 1
    nout = 1

    def __init__(self, K, *inputs, premul=False, **kwargs):
        super().__init__(nin=1, nout=1, inputs=inputs, **kwargs)

        self.premul = premul
        self.K  = self._param('K', K, min=-3.0, max=3.0)
        
    def output(self, t=None):
        input = self.inputs[0]
        
        if isinstance(input, np.ndarray) and isinstance(self.K, np.ndarray):
            # array x array case
            if self.premul:
                # premultiply by gain
                return [self.K @ input]
            else:
                # postmultiply by gain
                return [input @ self.K]
        else:
            return [self.inputs[0] * self.K]