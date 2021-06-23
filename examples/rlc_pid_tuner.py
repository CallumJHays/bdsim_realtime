
from typing import Union

from bdsim import BlockDiagram, Block, Plug, BDSim
from bdsim.components import Clock

import bdsim_realtime

Signal = Union[Block, Plug]

# first loop
# ADC_PIN = const(36)
# PWM_PIN = const(23) # This PWM is BROKEN on mine

# second loop
# ADC_PIN = const(39)
# PWM_PIN = const(22)

GPIO_V = 3.3

FREQ = 50
# offsets chosen after observing execution
ADC_OFFSET          = 0.0
CONTROLLER_OFFSET   = 0.015 # adc + gc.collect() execution takes <= 15ms
PWM_OFFSET          = 0.027 # controller execution takes <= 12ms
DATASENDER_OFFSET   = 0.039 # execution takes <= 12ms

# R = 4.7e3
# L = 47e-4 # +- 5%
# C = 100e-6

DEFAULT_KP = 1.0
DEFAULT_KI = 1.0
# DEFAULT_KD = 1.0

# def vc_rlc(bd: BlockDiagram, V_s: Signal, r: float, l: float, c: float):
#     "Transfer function for voltage across a capacitor in an RLC circuit"
#     return bd.LTI_SISO(1, [l * c, r * c, 1], V_s)

def discrete_pi_controller(bd: BlockDiagram, clock: Clock, p: float, i: float, *, min: float = -float('inf'), max=float('inf')):
    "Discrete PI Controller"
    p_term = bd.TUNABLE_GAIN(p, tinker=True)
    i_term = bd.DINTEGRATOR(clock)

    input = bd.CLIP(
        bd.SUM('++', p_term, bd.TUNABLE_GAIN(i, i_term, tinker=True)),
        min=min, max=max
    )

    def register_err(err: Signal):
        p_term[0] = err
        i_term[0] = err

    return input, register_err



def control_rlc(bd: BlockDiagram, reference: Signal, kp: float, ki: float):
    "Use A PI Controller to try and track the input reference signal with the voltage over the capacitor"

    # adc = bd.ADC_ESP32(
    #     bd.clock(FREQ, offset=ADC_OFFSET, unit='Hz'),
    #     bit_width=12, v_max=3.6, pin=ADC_PIN)
    adc = reference

    duty, register_err = discrete_pi_controller(bd,
        bd.clock(FREQ, offset=CONTROLLER_OFFSET, unit='Hz'),
        kp, ki, min=0, max=1)

    # max frequency allowable by ESP32 for smoothest output
    # pwm_v = bd.PWM_ESP32(
    #     bd.clock(FREQ, offset=PWM_OFFSET, unit='Hz'),
    #     duty, freq=1000, v_on=3.3, pin=PWM_PIN)
    pwm_v = bd.GAIN(3.3, duty)

    # with simulation_only:
    #     V_c = vc_rlc(pwm_v, R, L, C)

    err = bd.SUM('+-', reference, adc)
    register_err(err)

    return adc, err, duty, pwm_v


if __name__ == "__main__":

    bd = BDSim().blockdiagram()

    with bdsim_realtime.tuning.TcpClientTuner() as tuner:

        target = bd.TUNABLE_WAVEFORM("sine", offset=1, tinker=True)

        adc, err, duty, _pwm_v = control_rlc(bd, target, DEFAULT_KP, DEFAULT_KI)

    bd.TUNERSCOPE(
        target, adc, err, duty,
        nin=4,
        labels=['Target', 'ADC', 'Error', 'Duty %'],
        name='PID Tuning live feedback',
        tuner=tuner)

    bdsim_realtime.run(bd, tuner=tuner)
