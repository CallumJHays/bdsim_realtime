# demo.py
import numpy as np
import os
import bdsim
import bdsim_realtime

# include bdsim_realtime blocks
os.environ['BDSIM_PATH'] = f"{os.environ.get('BDSIM_PATH', '')}:{bdsim_realtime.__path__}/blocks"

# setup block-diagram and tuner client
bd = bdsim.BDSim().blockdiagram()
tuner = bdsim_realtime.tuning.TcpClientTuner()

# use first local camera available
bgr = bd.CAMERA(0)

# display in web stream
bd.DISPLAY(bgr, name="BGR Stream", web_stream_host=tuner)

# tune system parameters in the web editor
gain = tuner.param(1, min=0, max=100)

# stream some telemetry data (random for demo)
data = bd.FUNCTION(
    lambda: (gain * np.random.rand(3)).tolist(),
    nout=3
)
bd.SCOPE(data[:], nin=3, tuner=tuner)

bdsim_realtime.run(bd)