from src.char.BaseChar import BaseChar, SwitchPriority

from rotation_axis import AxisController, reset_axis_for_task


class Douling(BaseChar):
    """Position 2 of the fixed Hsin/Douling/Rover rotation."""

    AXIS_POSITION = 2

    def reset_state(self):
        super().reset_state()
        reset_axis_for_task(self.task)

    def do_perform(self):
        AxisController.for_task(self.task).perform(self, self.AXIS_POSITION)

    def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
        return SwitchPriority.NO

