import bdsim, numpy as np
import bdsim_realtime

# setup block-diagram and tuner client
bd = bdsim.BDSim(packages="bdsim_realtime").blockdiagram()

# All TunableBlocks within this context manager will register their parameters swith the Tuner
with bdsim_realtime.tuning.tuners.TcpClientTuner() as tuner:
    # use first local camera available
    clock = bd.clock(24, unit='Hz')
    bgr = bd.CAMERA(0, clock=clock)

    # display in web stream
    bd.DISPLAY(bgr, name="BGR Stream", web_stream_host=tuner, show_fps=True)

    # tune system parameters in the web editor
    gain = tuner.param(1, min=0, max=100)

    # stream some telemetry data (random for demo)
    data = bd.FUNCTION(
        lambda _: (gain.val * np.random.rand(3)).tolist(),
        nin=1, # unused import required here to use function as a Clocked Source Block
        nout=3
    )
    bd.connect(bgr, data)

    bd.TUNERSCOPE(
        data[0], data[1], data[2],
        nin=3,
        labels=['x', 'y', 'z'],
        name='Random Data',
        tuner=tuner)

bd.compile() # perform verification
bdsim_realtime.run(bd, tuner=tuner) # run forever