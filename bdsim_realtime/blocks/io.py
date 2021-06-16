from enum import Enum
from typing import Any, Optional, Union
from typing_extensions import Literal
from machine import Pin, ADC as _ADC, PWM as _PWM

from bdsim.blocks.discrete import ZOH
from bdsim.blockdiagram import block
from bdsim.components import Block, Clock, Plug



# these will override the classes defined in bdsim.blocks.io
# as they have the same name and they necessarily are defined
# after the originals, therefore being later in the blocklist,
# overwriting the original.
@block
class DigitalIn(ZOH):
    
    def __init__(
        self,
        clock: Clock,
        inp: Optional[Union[Block, Plug]] = None,
        *,
        pin: Optional[int] = None,
        pull: Literal["up", "down"] = "up",
        **kwargs: Any
    ):
        assert pull in ("up", "down")
        super().__init__(nin=1 if inp else 0, nout=1, clock=clock, inputs=(inp,) if inp else (), **kwargs)

        assert pin
        self.pin = Pin(
            pin,
            Pin.IN,
            Pin.PULL_UP if pull == "up" else Pin.PULL_DOWN
        )
    
    def output(self):
        return [self.pin()]

@block
class DigitalOut(ZOH):
    def __init__(
        self,
        clock: Clock,
        inp: Optional[Union[Block, Plug]] = None,
        *,
        pin: Optional[int] = None,
        **kwargs: Any
    ):
        super().__init__(
            nin=1,
            nout=0,
            clock=clock,
            inputs=(inp,) if inp else (),
            **kwargs
        )

        assert pin # TODO
        self.pin = Pin(
            pin,
            Pin.OUT
        )
    
    def output(self):
        self.pin(self.inputs[0])

class AdcAtten(Enum):
    ATTN_0DB = _ADC.ATTN_0DB
    ATTN_2_5DB = _ADC.ATTN_2_5DB
    ATTN_6DB = _ADC.ATTN_6DB
    ATTN_11DB = _ADC.ATTN_11DB

class AdcWidth(Enum):
    WIDTH_9BIT = _ADC.WIDTH_9BIT
    WIDTH_10BIT = _ADC.WIDTH_10BIT
    WIDTH_11BIT = _ADC.WIDTH_11BIT
    WIDTH_12BIT = _ADC.WIDTH_12BIT

@block
class ADC(ZOH):

    def __init__(
        self,
        clock: Clock,
        inp: Optional[Union[Block, Plug]] = None,
        *,
        pin: Optional[int] = None,
        pull: Literal["up", "down"] = "up",
        # TODO: make this more generic across uPy devices
        # currently only made for ESP32
        atten: AdcAtten = AdcAtten.ATTN_0DB,
        width: int = 12,
        **kwargs: Any
    ):
        if pin:
            # TODO: only works for ESP32
            assert 32 <= pin <= 39
        assert 9 <= width <= 12
        super().__init__(nin=1 if inp else 0, nout=1, inputs=(inp,) if inp else (), clock=clock, **kwargs)

        assert pin # TODO: sim difference etc

        self.adc = _ADC(Pin(
            pin,
            Pin.IN,
            Pin.PULL_UP if pull == "up" else Pin.PULL_DOWN
        ))
        
        # TODO: make this more generic across uPy devices
        # currently only made for ESP32
        self.adc.atten(atten)
        self.atten_gain = 1. if atten is AdcAtten.ATTN_0DB else \
            1.34 if atten is AdcAtten.ATTN_2_5DB else \
            2. if atten is AdcAtten.ATTN_6DB else \
            3.6 # if atten is AdcAtten.ATTN_11DB 
        self.adc.width(getattr(AdcWidth, "WIDTH_{}BIT".format(width)))
        self.width = width
    
    def output(self):
        "returns the voltage read at this pin"
        return (self.adc.read() / self.width) * self.atten_gain

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
@block
class PWM(ZOH):

    def __init__(
        self,
        clock: Clock,
        inp: Optional[Union[Block, Plug]] = None,
        *,
        freq: int,
        pin: Optional[int] = None,
        **kwargs: Any
    ):
        freq = int(freq) # convert for convenience (so 1eX can be used)
        assert 1 <= freq <= 40000000 # 1 - 40mhz
        super().__init__(nin=1, nout=0, inputs=(inp,), clock=clock, **kwargs)

        assert pin #TODO: not just esp32
        self.pwm = _PWM(Pin(pin, Pin.OUT), freq, 0)
        
    def output(self):
        # TODO: sim implementation in upstream bdsim which this subclasses and overwrites
        """
        In sim mode: returns True if high or False if low. Otherwise return None.
        Only Plant()s can be connected to this output.
        """
        self.pwm.duty(
            round(self.inputs[0] * 1023)
        )