import math

from bdsim.components import SourceBlock, block

from bdsim_realtime.tuning.tunable_block import TunableBlock


@block
class Tunable_Waveform(SourceBlock, TunableBlock):
    """
    :blockname:`WAVEFORM`
    
    .. table::
       :align: left
    
    +--------+---------+---------+
    | inputs | outputs |  states |
    +--------+---------+---------+
    | 0      | 1       | 0       |
    +--------+---------+---------+
    |        | float   |         | 
    +--------+---------+---------+
    """

    type = "waveform"

    def __init__(self, wave='square',
                 freq=1, unit='Hz', phase=0, amplitude=1, offset=0,
                 min=None, max=None, duty=0.5,
                 **kwargs):
        """
        :param wave: type of waveform to generate: 'sine', 'square' [default], 'triangle'
        :type wave: str, optional
        :param freq: frequency, defaults to 1
        :type freq: float, optional
        :param unit: frequency unit, can be 'rad/s', defaults to 'Hz'
        :type unit: str, optional
        :param amplitude: amplitude, defaults to 1
        :type amplitude: float, optional
        :param offset: signal offset, defaults to 0
        :type offset: float, optional
        :param phase: Initial phase of signal in the range [0,1], defaults to 0
        :type phase: float, optional
        :param min: minimum value, defaults to 0
        :type min: float, optional
        :param max: maximum value, defaults to 1
        :type max: float, optional
        :param duty: duty cycle for square wave in range [0,1], defaults to 0.5
        :type duty: float, optional
        :param ``**kwargs``: common Block options
        :return: a WAVEFORM block
        :rtype: WaveForm instance
        
        Create a waveform generator block.

        Examples::
            
            WAVEFORM(wave='sine', freq=2)   # 2Hz sine wave varying from -1 to 1
            WAVEFORM(wave='square', freq=2, unit='rad/s') # 2rad/s square wave varying from -1 to 1
            
        The minimum and maximum values of the waveform are given by default in
        terms of amplitude and offset. The signals are symmetric about the offset 
        value. For example::
            
            WAVEFORM(wave='sine') varies between -1 and +1
            WAVEFORM(wave='sine', amplitude=2) varies between -2 and +2
            WAVEFORM(wave='sine', offset=1) varies between 0 and +2
            WAVEFORM(wave='sine', amplitude=2, offset=1) varies between -1 and +3
            
        Alternatively we can specify the minimum and maximum values which override
        amplitude and offset::
            
            WAVEFORM(wave='triangle', min=0, max=5) varies between 0 and +5
        
        At time 0 the sine and triangle wave are zero and increasing, and the
        square wave has its first rise.  We can specify a phase shift with 
        a number in the range [0,1] where 1 corresponds to one cycle.
        """
        super().__init__(nout=1, **kwargs)

        self.duty = self._param('duty', duty, min=0.0, max=1.0)
        self.wave = self._param('wave', wave, oneof=['square', 'triangle', 'sine'])
        self.freq = self._param('freq', freq, min=1.0, max=50.0)
        self.phase = self._param('phase', phase, min=0.0, max=1.0)
        self.amplitude = self._param('amplitude', amplitude, min=0.0, max=3.0)
        self.offset = self._param('offset', offset, min=-5, max=5)

        assert unit in ('Hz', 'rad/s')
        self.unit = unit


    def output(self, t=None):
        phase = (t * self.freq - self.phase ) % 1.0
        
        # define all signals in the range -1 to 1
        if self.wave == 'square':
            if phase < self.duty:
                out = 1
            else:
                out = -1
        elif self.wave == 'triangle':
            if phase < 0.25:
                out = phase * 4
            elif phase < 0.75:
                out = 1 - 4 * (phase - 0.25)
            else:
                out = -1 + 4 * (phase - 0.75)
        elif self.wave == 'sine':
            out = math.sin(phase*2*math.pi)
        else:
            raise ValueError('bad option for signal')

        out = out * self.amplitude + self.offset

        #print('waveform = ', out)
        return [out]