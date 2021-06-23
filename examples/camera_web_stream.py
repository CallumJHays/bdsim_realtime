import os
import bdsim
import bdsim_realtime

# include bdsim_realtime blocks
os.environ['BDSIM_PATH'] = f"{os.environ.get('BDSIM_PATH', '')}:{bdsim_realtime.__path__}/blocks"

# setup block-diagram and tuner client
# note we need to create a blockdiagram through the sim object because
# the BlockDiagram class doesn't load new blocks from BDSIM_PATH; only BDSim does.
bd = bdsim.BDSim().blockdiagram()
tuner = bdsim_realtime.tuning.TcpClientTuner()

# use first local camera available
bgr = bd.CAMERA(0, clock=bd.clock(30, unit='Hz'))

# display in web stream
bd.DISPLAY(bgr, name="BGR Stream", web_stream_host=tuner)

bdsim_realtime.run(bd, tuner=tuner)