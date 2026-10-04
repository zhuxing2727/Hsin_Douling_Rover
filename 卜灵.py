import time

from src.char.BaseChar import BaseChar


class Douling(BaseChar):
    """2号位卜灵：aaaa -> EaZQR，完成后切到3号位。"""

    AXIS_POSITION = 2
    NORMAL_INTERVAL = 0.12
    NORMAL_ATTACK_FINISH_WAIT = 0.2
    HEAVY_DURATION = 1.0
    SWITCH_TIMEOUT = 2.5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._axis_count = 0
        self._axis_combat_start = None

    def _prepare_axis(self):
        combat_start = getattr(self.task, "combat_start", None)
        if combat_start != self._axis_combat_start:
            previous = self._axis_combat_start
            self._axis_combat_start = combat_start
            self._axis_count = 0
            if previous is not None:
                self.task._fixed_axis_started = False

    def _normal_attack_with_wait(self):
        self.normal_attack()
        self.sleep(self.NORMAL_INTERVAL)
        self.sleep(self.NORMAL_ATTACK_FINISH_WAIT, False)

    def _normal_attack_retry(self):
        self.normal_attack()
        self.sleep(self.NORMAL_INTERVAL)

    def _normal_chain(self, count):
        for _ in range(count):
            self._normal_attack_with_wait()

    def _wait_ready(self, predicate):
        while True:
            self.check_combat()
            if predicate():
                return True
            self._normal_attack_retry()

    def _resonance(self):
        self._wait_ready(self.resonance_available)
        return bool(self.click_resonance(time_out=1.5)[0])

    def _echo(self):
        if self.echo_available():
            self.click_echo(time_out=0)
        return True

    def _liberation(self):
        while True:
            self._wait_ready(self.liberation_available)
            if self.click_liberation(wait_if_cd_ready=0.2):
                return True
            self._normal_attack_retry()

    def _heavy(self):
        self.heavy_attack(self.HEAVY_DURATION)
        return True

    def _reset_team_axis(self):
        for char in getattr(self.task, "chars", []):
            if char is not None and hasattr(char, "_axis_count"):
                char._axis_count = 0
                char._axis_combat_start = self._axis_combat_start

    def _switch_to_slot(self, slot):
        target_index = slot - 1
        self.has_intro = False
        self.has_sub_dps_intro = False
        self._liberation_available = self.liberation_available()
        self.use_tool_box()
        start = time.time()
        while time.time() - start < self.SWITCH_TIMEOUT:
            in_team, current_index, _ = self.task.in_team()
            if in_team and current_index == target_index:
                now = time.time()
                self.last_switch_time = now
                for char in getattr(self.task, "chars", []):
                    if char is None:
                        continue
                    char.is_current_char = char.index == target_index
                    if char.index == target_index:
                        char.last_switch_in_time = now
                return True
            self.task.send_key(str(slot))
            self.task.next_frame()
            self.sleep(0.1, False)
        self.logger.warning("Douling fixed-axis switch to slot %s timed out", slot)
        return False

    def _finish(self, success):
        if success:
            self._axis_count += 1
            self.task._fixed_axis_started = True
            self._switch_to_slot(3)
        else:
            self.logger.warning("Douling fixed-axis action failed; restarting at slot 2")
            self.task._fixed_axis_started = False
            self._reset_team_axis()
            self._switch_to_slot(2)

    def _perform_axis(self):
        self._normal_chain(4)
        if not self._resonance():
            return False
        self._normal_attack_with_wait()
        self._heavy()
        self._echo()
        return self._liberation()

    def _ensure_start_slot(self):
        in_team, current_index, _ = self.task.in_team()
        if not in_team or current_index != 1:
            self._switch_to_slot(2)
            return False
        return True

    def do_perform(self):
        self._prepare_axis()
        if self._axis_count == 0 and not self._ensure_start_slot():
            return
        if self.has_intro:
            self.wait_intro(1.2)
        self._finish(self._perform_axis())

    def on_combat_end(self, chars):
        self._axis_count = 0
        self._axis_combat_start = None
        self.task._fixed_axis_started = False
