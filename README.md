# BDSim Realtime

Real-time execution and remote monitoring and tuning of BDSim Block-Diagrams for modelling and control of Dynamical Systems.
See https://github.com/petercorke/bdsim for the base framework and simulation package.

TODO: more docs

## BDSim Web-Tuner

Web-based telemetry and parameter tuning interface for BDSim

![Demo](./demo.gif)

Note: Screen-recording lead to low FPS - usual FPS was around 30 on the laptop used (max for webcam).

Note: under heavy development (pre-alpha). These instructions will not fully work at the time of writing, but is supposed to give an idea of the usage once released.

## Installation

```bash
pip install "bdsim_realtime[opencv]" # opencv optional
```


## Usage

First, start the server and keep it running:

```bash
python -m bdsim_realtime.webapp
```

Then, add and run your bdsim script, 

```python
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
```

Now access the tuner at [http://localhost:8080](http://localhost:8080)


## Development

### Setup


```bash
python -m venv .venv # create venv
source .venv/bin/activate # activate venv

pip install -e ".[opencv]" # install in editable symlink mode
npm i # install JS deps
```

#### Frontend

```
npm run dev # run hot-reloaded app
```

#### Backend

Same as non-development version. Run:

```
python -m bdsim_realtime.webapp
```

And then run your example / test script:

```
python examples/blob_detector_tuner.py
```