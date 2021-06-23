from abc import ABC, abstractmethod
from typing import List, Optional
from ..parameter import Param

global_current_tuner: Optional['Tuner'] = None

class Tuner(ABC):

    def __init__(self):
        self.queued_updates = []
        self.gui_params: List[Param] = []
        self._prev_tuner: Optional[Tuner] = None

    def setup(self):
        # if needed
        pass

    def __enter__(self):
        global global_current_tuner
        self._prev_tuner = global_current_tuner
        global_current_tuner = self
        return self
    
    def __exit__(self, *_):
        global global_current_tuner
        global_current_tuner = self._prev_tuner
        self._prev_tuner = None
        

    def update(self):
        for update in self.queued_updates:
            update()
        self.queued_updates = []

    def queue_update(self, update_fn):
        self.queued_updates.append(update_fn)

    @abstractmethod
    def register_video_stream(self, feed_fn, name):
        pass


    @abstractmethod
    def register_signal_scope(self, feed_fn, name):
        pass

    @abstractmethod
    def queue_signal_update(self, id, t, data):
        pass

    # TODO: save_params() and load_params()
    def param(self, init, name=None, min=None, max=None, log_scale=False, step=None, oneof=None, default=None, force_gui=False):
        """Create a parameter and register it with the blockdiagram engine

        Most keyword arguments passed here will override the sensible defaults for params used by TunableBlocks,
        so use with caution!

        :param init: Initial value of the param.
        :param name: name of the param. If provided, will become the label on the gui - otherwise will be list of "block.param" where it is used by blocks, defaults to None
        :param min: minimum of the value. If provided with max, a GUI can present a slider control, defaults to None
        :param max: maximum of the value. If provided with max, a GUI can present a slider control, defaults to None
        :param log_scale: Whether or not to use a log-scaling slider. will override 'step', defaults to False
        :param step: the step interval of a slider. Disabled by 'log_scale' if  provided, defaults to None
        :param oneof: a list or tuple of options. Will produce a dropdown menu if provided, defaults to None
        :param default: the default value for an OptionalParam. Setting this allows '*init' to be None. Will produce a controls shown/hidden by an .enabled checkbox - switching the value between None and it's underlying value when enabled, defaults to None :class:`.Param`], optional
        :param force_gui: If a parameter is not used by any blocks, it will not be shown in a gui. set this True to override this behaviour, defaults to False

        :return: returns a :class:`.Param` object that may then be passed into a :class:`.TunableBlock` for use.
        :rtype: :class:`.Param`
        """

        kwargs = {k: v for k, v in dict(name=name, created_by_user=True, min=min, max=max, step=step,
                                        log_scale=log_scale, oneof=oneof, default=default).items()
                  if v is not None}

        param = Param(init, **kwargs)

        # if `force_gui`, include the gui control at the index of insertion,
        # even if it's not used by any blocks.
        if force_gui:
            self.gui_params.append(param)

        return param