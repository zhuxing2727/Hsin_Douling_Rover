from ok import Logger
from src.char.BaseChar import BaseChar, Elements, SwitchPriority

from rotation_axis import AxisController, reset_axis_for_task


_ROVER_FORM_NAMES = {
    Elements.SPECTRO: "Rover: Spectro",
    Elements.WIND: "Rover: Aero",
    Elements.HAVOC: "Rover: Havoc",
}


class Rover(BaseChar):
    """Position 3 of the fixed Hsin/Douling/Rover rotation."""

    AXIS_POSITION = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ring_index = -1
        self._bind_form_logger()

    def reset_state(self):
        self.ring_index = -1
        super().reset_state()
        reset_axis_for_task(self.task)
        self._bind_form_logger()

    @property
    def display_name(self):
        return _ROVER_FORM_NAMES.get(self.ring_index, "Rover")

    def __repr__(self):
        return self.display_name

    def _bind_form_logger(self):
        self.logger = Logger.get_logger(self.display_name)

    def init(self):
        if hasattr(self.task, "_ensure_ring_index"):
            self.task._ensure_ring_index()
            self._bind_form_logger()

    def do_perform(self):
        self.init()
        AxisController.for_task(self.task).perform(self, self.AXIS_POSITION)

    def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
        return SwitchPriority.NO
