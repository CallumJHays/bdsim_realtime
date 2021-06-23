from typing import TYPE_CHECKING

from bdsim.components import SinkBlock, block

if TYPE_CHECKING:
    from ..tuning import Tuner
    

@block
class TunerScope(SinkBlock):
    """
    :blockname:`TUNERSCOPE`

    .. table::
       :align: left

       +--------+---------+---------+
       | inputs | outputs |  states |
       +--------+---------+---------+
       | 1      | 0       | 0       |
       +--------+---------+---------+
       | float, |         |         | 
       | A(N,)  |         |         | 
       +--------+---------+---------+
    """

    def __init__(
        self,
        *inputs,
        nin=None,
        styles=None,
        labels=None,
        tuner: 'Tuner',
        **kwargs
    ):
        """
        Create a block that plots input ports against time.

        :param nin: number of inputs, defaults to length of style vector if given,
                    otherwise 1
        :type nin: int, optional
        :param styles: styles for each line to be plotted
        :type styles: optional str or dict, list of strings or dicts; one per line
        :param scale: y-axis scale, defaults to 'auto'
        :type scale: 2-element sequence
        :param labels: vertical axis labels
        :type labels: sequence of strings
        :param grid: draw a grid, default is on. Can be boolean or a tuple of 
                     options for grid()
        :type grid: bool or sequence
        :param ``*inputs``: Optional incoming connections
        :type ``*inputs``: Block or Plug
        :param ``**kwargs``: common Block options
        :return: A SCOPE block
        :rtype: Scope instance

        Create a block that plots input ports against time.  

        Each line can have its own color or style which is specified by:

            - a dict of options for `Line2D <https://matplotlib.org/3.2.2/api/_as_gen/matplotlib.lines.Line2D.html#matplotlib.lines.Line2D>`_ or 
            - a  MATLAB-style linestyle like 'k--'

        If multiple lines are plotted then a heterogeneous list of styles, dicts or strings,
        one per line must be given.

        The vertical scale factor defaults to auto-scaling but can be fixed by
        providing a 2-tuple [ymin, ymax]. All lines are plotted against the
        same vertical scale.

        Examples::

            SCOPE()
            SCOPE(nin=2)
            SCOPE(nin=2, scale=[-1,2])
            SCOPE(style=['k', 'r--'])
            SCOPE(style='k--')
            SCOPE(style={'color:', 'red, 'linestyle': '--''})

        .. figure:: ../../figs/Figure_1.png
           :width: 500px
           :alt: example of generated graphic

           Example of scope display.
        """

        self.type = 'scope'
        if styles is not None:
            self.styles = list(styles)
            if nin is not None:
                assert nin == len(styles), 'need one style per input'
            else:
                nin = len(styles)

        if labels is not None:
            self.labels = list(labels)
            if nin is not None:
                assert nin == len(labels), 'need one label per input'
            else:
                nin = len(labels)
        else:
            self.labels = labels

        if nin is None:
            nin = 1

        super().__init__(nin=nin, inputs=inputs, **kwargs)

        self.tuner = tuner
        self.scope_id = tuner.register_signal_scope(self.name, nin, styles=styles, labels=labels) \
            if tuner else None
            
        # TODO, wire width
        # inherit names from wires, block needs to be able to introspect

    def step(self):
        # inputs are set
        self.tuner.queue_signal_update(self.scope_id, self.bd.state.t, self.inputs)

