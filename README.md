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
pip i -r requirements.txt # use Python >= 3.6
npm i # install JS deps
npm run build # build optimized bundle
```

## Usage

First, start the server and keep it running:

```bash
python server.py --host=0.0.0.0 --app-port=8080
```

Next, (in a separate terminal) install [BDSim](httpsserver://github.com/petercorke/bdsim) with `pip install bdsim`. Then define a block-diagram and link it to the tuner:

```python
# demo.py
import bdsim, numpy as np

# setup block-diagram and tuner client
bd = bdsim.BlockDiagram()
tuner = bdsim.tuning.tuners.TcpClientTuner()

# use first local camera available
bgr = bd.CAMERA(0)

# display in web stream
bd.DISPLAY(bgr, name="BGR Stream", web_stream_host=tuner)

# tune system parameters in the web editor
gain = bd.param(1, min=0, max=100)

# stream some telemetry data (random for demo)
data = bd.FUNCTION(
    lambda: (gain * np.random.rand(3)).tolist(),
    nout=3
)
bd.SCOPE(data[:], nin=3, tuner=tuner)

bd.compile() # perform verification
bd.run_realtime() # run forever
```

Now access the tuner at [http://localhost:8080]()
