import time

from src.char.BaseChar import BaseChar, SwitchPriority


_STARTUP = ((2, ("a", "a", "a", "a", "E", "a", "Z", "Q", "R")), (3, ("E", "a", "a", "a", "a")), (1, ("a", "a")), (3, ("E", "R", "Q")), (1, ("a", "a", "a", "a", "Z", "R", "a", "E", "E", "a", "a", "F", "a", "a", "a", "Z", "R")))
_LOOP = ((3, ("E", "a")), (2, ("a", "a", "a", "a", "E", "a", "Z", "Q", "R")), (3, ("E", "R", "Q")), (1, ("a", "a", "a", "a", "Z", "R", "a", "E", "E", "a", "a", "F", "a", "a", "a", "Z", "R")))


class _AxisState:
    def __init__(self):
        self.phase, self.index = "startup", 0

    def steps(self):
        return _STARTUP if self.phase == "startup" else _LOOP

    def advance(self):
        self.index += 1
        if self.phase == "startup" and self.index == len(_STARTUP):
            self.phase, self.index = "loop", 0
        elif self.phase == "loop" and self.index == len(_LOOP):
            self.index = 0


def _state(task):
    value = getattr(task, "_fixed_rotation_state", None)
    if value is None or not all(hasattr(value, x) for x in ("phase", "index", "steps", "advance")):
        value = _AxisState()
        setattr(task, "_fixed_rotation_state", value)
    return value


def _reset(task):
    value = _state(task)
    value.phase, value.index = "startup", 0


def _call(obj, name, *args, **kwargs):
    method = getattr(obj, name, None)
    if method is None:
        return None
    try:
        return method(*args, **kwargs)
    except TypeError:
        return method(*args)


def _sleep(char, seconds):
    method = getattr(char, "sleep", None)
    (method or time.sleep)(seconds)


def _heavy(char):
    task = char.task
    down, up = getattr(task, "mouse_down", None), getattr(task, "mouse_up", None)
    if down is None or up is None:
        _call(char, "heavy_attack")
        return
    _call(char, "check_combat")
    down()
    try:
        started = time.time()
        while time.time() - started < 1.0:
            if getattr(char, "flying", lambda: False)():
                break
            _sleep(char, 0.05)
    finally:
        up()
    _sleep(char, 0.01)
    if getattr(char, "flying", lambda: False)():
        _call(char, "wait_down")


def _action(char, action):
    if action == "a":
        _call(char, "cycle_start"); _call(char, "click"); _call(char, "cycle_sleep")
    elif action == "E":
        _call(char, "check_combat"); _call(char, "click_resonance", send_click=True, time_out=0)
    elif action == "Z":
        _heavy(char)
    elif action == "Q":
        _call(char, "click_echo", time_out=0)
    elif action == "R":
        _call(char, "click_liberation", send_click=True)
    elif action == "F":
        for name in ("click_execution", "click_forte", "execute"):
            method = getattr(char, name, None)
            if method:
                method(); break
        else:
            for name in ("press_key", "key_press", "send_key", "press"):
                method = getattr(char.task, name, None)
                if method:
                    try: method("f")
                    except TypeError: method("F")
                    break


def _switch(char, current, target):
    if current == target:
        return
    chars = getattr(char.task, "chars", ())
    actual = next((i for i, item in enumerate(chars, 1) if item is char), current)
    count = (target - actual) % 3 or 3
    for index in range(count):
        char.switch_next_char()
        if index + 1 < count: _sleep(char, 0.05)


def _perform_axis(char, position):
    state = _state(char.task)
    target, actions = state.steps()[state.index]
    if target != position:
        _switch(char, position, target)
        return
    for action in actions: _action(char, action)
    state.advance()
    _switch(char, position, state.steps()[state.index][0])


class Douling(BaseChar):
    AXIS_POSITION = 2

    def reset_state(self):
        super().reset_state()
        _reset(self.task)

    def do_perform(self):
        _perform_axis(self, self.AXIS_POSITION)

    def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
        return SwitchPriority.NO
