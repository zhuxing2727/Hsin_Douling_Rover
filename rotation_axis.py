"""Fixed three-character combat rotation.

The project that consumes these character classes owns the real ``BaseChar``
implementation.  This module only owns the shared rotation state and the
small action adapter used by the three characters.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class AxisStep:
    position: int
    owner: str
    actions: tuple[str, ...]


STARTUP_AXIS: tuple[AxisStep, ...] = (
    AxisStep(2, "Douling", ("a", "a", "a", "a", "E", "a", "Z", "Q", "R")),
    AxisStep(3, "Rover", ("E", "a", "a", "a", "a")),
    AxisStep(1, "Hsin", ("a", "a")),
    AxisStep(3, "Rover", ("E", "R", "Q")),
    AxisStep(
        1,
        "Hsin",
        (
            "a", "a", "a", "a", "Z", "R", "a", "E", "E", "a", "a", "F",
            "a", "a", "a", "Z", "R",
        ),
    ),
)

LOOP_AXIS: tuple[AxisStep, ...] = (
    AxisStep(3, "Rover", ("E", "a")),
    AxisStep(2, "Douling", ("a", "a", "a", "a", "E", "a", "Z", "Q", "R")),
    AxisStep(3, "Rover", ("E", "R", "Q")),
    AxisStep(
        1,
        "Hsin",
        (
            "a", "a", "a", "a", "Z", "R", "a", "E", "E", "a", "a", "F",
            "a", "a", "a", "Z", "R",
        ),
    ),
)

VALID_ACTIONS = frozenset(("a", "E", "Z", "Q", "R", "F"))


class AxisState:
    """Mutable state for one battle task."""

    def __init__(self) -> None:
        self.phase = "startup"
        self.step_index = 0

    @property
    def steps(self) -> tuple[AxisStep, ...]:
        return STARTUP_AXIS if self.phase == "startup" else LOOP_AXIS

    @property
    def current(self) -> AxisStep:
        return self.steps[self.step_index]

    def reset(self) -> None:
        self.phase = "startup"
        self.step_index = 0

    def advance(self) -> AxisStep:
        self.step_index += 1
        if self.phase == "startup" and self.step_index >= len(STARTUP_AXIS):
            self.phase = "loop"
            self.step_index = 0
        elif self.phase == "loop" and self.step_index >= len(LOOP_AXIS):
            self.step_index = 0
        return self.current


_STATES: dict[int, AxisState] = {}


def reset_axis_for_task(task: object) -> None:
    """Reset the fixed axis when a battle/task is reset."""

    state = _STATES.get(id(task))
    if state is None:
        state = AxisState()
        _STATES[id(task)] = state
    state.reset()
    try:
        setattr(task, "_fixed_rotation_state", state)
    except (AttributeError, TypeError):
        pass


def _state_for_task(task: object) -> AxisState:
    state = getattr(task, "_fixed_rotation_state", None)
    if isinstance(state, AxisState):
        return state
    state = _STATES.setdefault(id(task), AxisState())
    try:
        setattr(task, "_fixed_rotation_state", state)
    except (AttributeError, TypeError):
        pass
    return state


def _log(char: object, message: str) -> None:
    logger = getattr(char, "logger", None)
    if logger is not None and hasattr(logger, "debug"):
        logger.debug(message)


def _call_with_fallback(obj: object, name: str, *args: object, **kwargs: object) -> object:
    method = getattr(obj, name, None)
    if method is None:
        return None
    try:
        return method(*args, **kwargs)
    except TypeError:
        return method(*args)


def _sleep(char: object, seconds: float) -> None:
    method = getattr(char, "sleep", None)
    if method is not None:
        method(seconds)
    else:
        time.sleep(seconds)


def _normal_attack(char: object) -> None:
    _call_with_fallback(char, "cycle_start")
    _call_with_fallback(char, "click")
    _call_with_fallback(char, "cycle_sleep")


def _heavy_attack(char: object, duration: float = 1.0) -> None:
    """Execute Z as a protected long press of the normal-attack button."""

    _call_with_fallback(char, "check_combat")
    task = getattr(char, "task", None)
    mouse_down = getattr(task, "mouse_down", None)
    mouse_up = getattr(task, "mouse_up", None)
    if mouse_down is None or mouse_up is None:
        _call_with_fallback(char, "heavy_attack")
        return

    mouse_down()
    started = time.time()
    try:
        while time.time() - started < duration:
            flying = getattr(char, "flying", None)
            if flying is not None and flying():
                break
            _sleep(char, 0.05)
    finally:
        mouse_up()
    _sleep(char, 0.01)
    flying = getattr(char, "flying", None)
    if flying is not None and flying():
        _call_with_fallback(char, "wait_down")


def _resonance(char: object) -> None:
    _call_with_fallback(char, "check_combat")
    _call_with_fallback(char, "click_resonance", send_click=True, time_out=0)


def _echo(char: object) -> None:
    _call_with_fallback(char, "click_echo", time_out=0)


def _liberation(char: object) -> None:
    _call_with_fallback(char, "click_liberation", send_click=True)


def _execution(char: object) -> None:
    """Press the project's execution key through whichever task API exists."""

    for name in ("click_execution", "click_forte", "execute"):
        method = getattr(char, name, None)
        if method is not None:
            method()
            return

    task = getattr(char, "task", None)
    for name in ("press_key", "key_press", "send_key", "press"):
        method = getattr(task, name, None)
        if method is None:
            continue
        try:
            method("f")
        except TypeError:
            method("F")
        return
    _log(char, "fixed axis F action skipped: no execution-key API is available")


def execute_actions(char: object, actions: Sequence[str]) -> None:
    for action in actions:
        if action == "a":
            _normal_attack(char)
        elif action == "E":
            _resonance(char)
        elif action == "Z":
            _heavy_attack(char)
        elif action == "Q":
            _echo(char)
        elif action == "R":
            _liberation(char)
        elif action == "F":
            _execution(char)
        else:
            raise ValueError(f"Unknown fixed-axis action: {action!r}")


class AxisController:
    """Run exactly one fixed-axis step and switch to its next target."""

    def __init__(self, task: object) -> None:
        self.task = task
        self.state = _state_for_task(task)

    @classmethod
    def for_task(cls, task: object) -> "AxisController":
        return cls(task)

    @property
    def current_step(self) -> AxisStep:
        return self.state.current

    def reset(self) -> None:
        self.state.reset()

    def perform(self, char: object, position: int) -> bool:
        step = self.state.current
        if step.position != position:
            _log(
                char,
                f"fixed axis waiting: current step is {step.owner}@{step.position}, "
                f"called by position {position}",
            )
            self._switch_to_position(char, position, step.position)
            return False

        _log(char, f"fixed axis {self.state.phase}[{self.state.step_index}] {step.actions}")
        execute_actions(char, step.actions)
        next_step = self.state.advance()
        self._switch_to_position(char, position, next_step.position)
        return True

    def _position_of(self, char: object) -> Optional[int]:
        chars = getattr(self.task, "chars", None)
        if chars is None:
            return None
        for index, item in enumerate(chars, start=1):
            if item is char:
                return index
        return None

    def _switch_to_position(self, char: object, current: int, target: int) -> None:
        if current == target:
            return
        actual = self._position_of(char) or current
        steps = (target - actual) % 3
        if steps == 0:
            steps = 3
        switch = getattr(char, "switch_next_char", None)
        if switch is None:
            raise AttributeError("BaseChar.switch_next_char is required by the fixed axis")
        for index in range(steps):
            switch()
            if index + 1 < steps:
                _sleep(char, 0.05)


def validate_axis() -> list[str]:
    """Return validation errors for the fixed startup/loop specification."""

    errors: list[str] = []
    for phase, steps in (("startup", STARTUP_AXIS), ("loop", LOOP_AXIS)):
        for index, step in enumerate(steps):
            if step.position not in (1, 2, 3):
                errors.append(f"{phase}[{index}] has invalid position {step.position}")
            if not step.actions:
                errors.append(f"{phase}[{index}] is empty")
            unknown = set(step.actions) - VALID_ACTIONS
            if unknown:
                errors.append(f"{phase}[{index}] has unknown actions {sorted(unknown)}")
    expected_startup = (2, 3, 1, 3, 1)
    expected_loop = (3, 2, 3, 1)
    expected_startup_actions = (
        ("a", "a", "a", "a", "E", "a", "Z", "Q", "R"),
        ("E", "a", "a", "a", "a"),
        ("a", "a"),
        ("E", "R", "Q"),
        ("a", "a", "a", "a", "Z", "R", "a", "E", "E", "a", "a", "F", "a", "a", "a", "Z", "R"),
    )
    expected_loop_actions = (
        ("E", "a"),
        ("a", "a", "a", "a", "E", "a", "Z", "Q", "R"),
        ("E", "R", "Q"),
        ("a", "a", "a", "a", "Z", "R", "a", "E", "E", "a", "a", "F", "a", "a", "a", "Z", "R"),
    )
    if tuple(step.position for step in STARTUP_AXIS) != expected_startup:
        errors.append("startup position order does not match the requested axis")
    if tuple(step.position for step in LOOP_AXIS) != expected_loop:
        errors.append("loop position order does not match the requested axis")
    if tuple(step.actions for step in STARTUP_AXIS) != expected_startup_actions:
        errors.append("startup action order does not match the requested axis")
    if tuple(step.actions for step in LOOP_AXIS) != expected_loop_actions:
        errors.append("loop action order does not match the requested axis")
    return errors
