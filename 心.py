import time

from src.char.BaseChar import BaseChar


class Hsin(BaseChar):
    """1号位心月狐：启动先 aa，之后执行 aaaaZR aEE aaF aaaZR。"""

    AXIS_POSITION = 1
    NORMAL_INTERVAL = 0.12
    NORMAL_ATTACK_FINISH_WAIT = 0.35
    FINAL_AA_GAP = 0.30
    HEAVY_DURATION = 1.0
    HEAVY_VERIFY_TIMEOUT = 1.0
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

    def _normal_chain(self, count):
        for _ in range(count):
            self._normal_attack_with_wait()

    def _final_aa(self):
        self._normal_attack_with_wait()
        self.sleep(self.FINAL_AA_GAP, False)
        self._normal_attack_with_wait()

    def _wait_ready(self, predicate):
        while True:
            self.check_combat()
            if predicate():
                return True
            self._normal_attack_with_wait()

    def _resonance(self):
        while True:
            self._wait_ready(self.resonance_available)
            result = self.click_resonance(
                has_animation=True,
                send_click=True,
                animation_min_duration=0.5,
                time_out=1.5,
            )
            if result and result[0]:
                return True
            self._normal_attack_with_wait()

    def _echo(self):
        if self.echo_available():
            self.click_echo(time_out=0)
        return True

    def _liberation(self):
        while True:
            self._wait_ready(self.liberation_available)
            if self.click_liberation(wait_if_cd_ready=0.2):
                return True
            self._normal_attack_with_wait()

    def _heavy(self):
        while True:
            forte_was_full = self.is_mouse_forte_full()
            self.heavy_attack(self.HEAVY_DURATION)
            if not forte_was_full:
                return True

            end = time.time() + self.HEAVY_VERIFY_TIMEOUT
            while time.time() < end:
                if not self.is_mouse_forte_full():
                    return True
                self.task.next_frame()
            self._normal_attack_with_wait()

    def _break(self):
        self.f_break()
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
        self.logger.warning("Hsin fixed-axis switch to slot %s timed out", slot)
        return False

    def _finish(self, success, next_slot):
        if success:
            self._axis_count += 1
            self._switch_to_slot(next_slot)
        else:
            self.logger.warning("Hsin fixed-axis action failed; restarting at slot 3")
            self._reset_team_axis()
            self._switch_to_slot(3)

    def _ensure_start_slot(self):
        in_team, current_index, _ = self.task.in_team()
        if not in_team or current_index != 1:
            self._switch_to_slot(2)
            return False
        return True

    def _final_segment(self):
        self._normal_chain(4)
        self._heavy()
        self._liberation()
        self._normal_chain(1)
        self._resonance()
        self._resonance()
        self._normal_chain(2)
        self._break()
        self._normal_chain(3)
        self._heavy()
        return self._liberation()

    def _perform_startup(self):
        self._normal_chain(2)
        return True

    def do_perform(self):
        self._prepare_axis()
        if not getattr(self.task, "_fixed_axis_started", False):
            self._switch_to_slot(2)
            return
        if self.has_intro:
            self.wait_intro(1.2)
        if self._axis_count == 0:
            self._finish(self._perform_startup(), 3)
        else:
            self._finish(self._final_segment(), 3)

    def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
        return super().get_switch_priority(current_char, has_intro, target_low_con)

    def on_combat_end(self, chars):
        self._axis_count = 0
        self._axis_combat_start = None
        self.task._fixed_axis_started = False
