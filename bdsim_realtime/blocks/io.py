from typing import Any, Optional, Union
from typing_extensions import Literal
# from machine import Pin, ADC as _ADC, PWM as _PWM
# import numpy as np

# import micropython

# from bdsim.blocks.discrete import ZOH
# from bdsim.blocks.io import ADC, PWM
# from bdsim.blockdiagram import block
# from bdsim.components import Block, Clock, ClockedBlock, Plug, SinkBlock



# these will override the classes defined in bdsim.blocks.io
# as they have the same name and they necessarily are defined
# after the originals, therefore being later in the blocklist,
# overwriting the original.


# TODO: write an abstract implementation and derive from it
# @block
# class DigitalIn_ESP32(ZOH):
    
#     def __init__(
#         self,
#         clock: Clock,
#         inp: Optional[Union[Block, Plug]] = None,
#         *,
#         pin: Optional[int] = None,
#         pull: Literal["up", "down"] = "up",
#         **kwargs: Any
#     ):
#         assert pull in ("up", "down")
#         super().__init__(nin=1 if inp else 0, nout=1, clock=clock, inputs=(inp,) if inp else (), **kwargs)

#         assert pin
#         self.pin = Pin(
#             pin,
#             Pin.IN,
#             Pin.PULL_UP if pull == "up" else Pin.PULL_DOWN
#         )
    
#     def output(self):
#         return [self.pin()]

# @block
# class DigitalOut_ESP32(SinkBlock, ClockedBlock):
#     "TODO: not finished or tested. probably wrong."

#     def __init__(
#         self,
#         clock: Clock,
#         inp: Optional[Union[Block, Plug]] = None,
#         *,
#         pin: Optional[int] = None,
#         **kwargs: Any
#     ):
#         super().__init__(
#             nin=1,
#             nout=0,
#             clock=clock,
#             inputs=(inp,) if inp else (),
#             **kwargs
#         )

#         assert pin # TODO
#         self.pin = Pin(
#             pin,
#             Pin.OUT
#         )
    
#     @micropython.native
#     def next(self):
#         self.pin(self.inputs[0])


# @block
# class ADC_ESP32(ADC):

#     # available attenuation configs result in these
#     # https://docs.micropython.org/en/latest/esp32/quickref.html#ADC.atten
#     V_RANGE2ATTEN = {
#         1.0: _ADC.ATTN_0DB,
#         1.34: _ADC.ATTN_2_5DB,
#         2.0: _ADC.ATTN_6DB,
#         3.6: _ADC.ATTN_11DB
#     }

#     def __init__(
#         self,
#         clock: Clock,
#         inp: Optional[Union[Block, Plug]] = None,
#         *,
#         pin: int,
#         v_max: float,
#         v_min: float = 0,
#         bit_width: int = 12,
#         pull: Literal["up", "down"] = "up",
#         # TODO: make this more generic across uPy devices
#         # currently only made for ESP32
#         **kwargs: Any
#     ):
#         assert 32 <= pin <= 39
#         assert 9 <= bit_width <= 12
#         super().__init__(
#             nin=1 if inp else 0,
#             nout=1,
#             inputs=(inp,) if inp else (),
#             clock=clock,
#             pin=pin,
#             v_min=v_min,
#             v_max=v_max,
#             bit_width=bit_width,
#             **kwargs)
#         self.bit_width = bit_width

#         self.adc = _ADC(Pin(
#             pin,
#             Pin.IN,
#             Pin.PULL_UP if pull == "down" else Pin.PULL_DOWN
#         ))

#         self.adc.atten(self.V_RANGE2ATTEN[self.v_range])
#         self.adc.width(getattr(_ADC, "WIDTH_{}BIT".format(bit_width)))
#         max_reading = 2 ** self.bit_width
#         self.radj = self.v_range / max_reading # reading adjustment constant

#     @micropython.native
#     def tick(self, dt: float):
#         "reset state to the voltage read at this pin"
#         self._x = float(self.adc.read()) * self.radj + self.v_min


# available on ESP32 uPy? ESP32 does have two...
# @block
# class DAC(ZOH):

#     def __init__(
#         self,
#         clock: Clock,
#         input: Union[Block, Plug],
#         *,
#         pin: int,

#     )
# @block
# class PWM_ESP32(PWM):

#     def __init__(
#         self,
#         clock: Clock,
#         duty_cycle: Optional[Union[Block, Plug]] = None,
#         *,
#         pin: int,
#         freq: int,
#         v_on: float,
#         duty0: int = 0,
#         v_off: float = 0,
#         **kwargs: Any
#     ):
#         assert 1 <= freq <= 40000000 # 1 - 40mhz
#         super().__init__(
#             nin=1,
#             nout=1,
#             duty_cycle=duty_cycle,
#             freq=freq,
#             v_off=v_off,
#             v_on=v_on,
#             approximate=True,
#             clock=clock,
#             **kwargs)

#         assert pin
#         self.pwm = _PWM(Pin(pin, Pin.OUT), freq, duty0)
    
#     def tick(self, dt: float):
#         self._x = self.inputs[0]
#         self.pwm.duty(round(self._x * 1023))
