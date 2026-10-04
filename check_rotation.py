"""Static checks for the generated fixed-axis modules."""

import ast
import py_compile
from pathlib import Path

from rotation_axis import AxisState, LOOP_AXIS, STARTUP_AXIS, validate_axis


ROOT = Path(__file__).resolve().parent
PY_FILES = ("rotation_axis.py", "卜灵.py", "雷主.py", "心.py", "check_rotation.py")


def main() -> None:
    errors = validate_axis()
    expected_classes = {"卜灵.py": "Douling", "雷主.py": "Rover", "心.py": "Hsin"}
    for filename in PY_FILES:
        path = ROOT / filename
        py_compile.compile(str(path), doraise=True)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if filename in expected_classes:
            classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
            expected = expected_classes[filename]
            if expected not in classes:
                errors.append(f"{filename} does not define {expected}")

    role_requirements = {
        "卜灵.py": ("send_key", "in_team", "normal_attack", "click_resonance", "click_echo", "click_liberation", "heavy_attack"),
        "雷主.py": ("send_key", "in_team", "normal_attack", "click_resonance", "click_echo", "click_liberation"),
        "心.py": ("send_key", "in_team", "normal_attack", "click_resonance", "click_echo", "click_liberation", "heavy_attack", "f_break"),
    }
    for filename, required in role_requirements.items():
        text = (ROOT / filename).read_text(encoding="utf-8")
        if "rotation_axis" in text:
            errors.append(f"{filename} must not depend on rotation_axis")
        for name in required:
            if name not in text:
                errors.append(f"{filename} is missing required BaseChar/task API: {name}")

    if tuple(step.position for step in STARTUP_AXIS) != (2, 3, 1, 3, 1):
        errors.append("startup axis position check failed")
    if tuple(step.position for step in LOOP_AXIS) != (3, 2, 3, 1):
        errors.append("loop axis position check failed")
    state = AxisState()
    for _ in STARTUP_AXIS:
        state.advance()
    if state.phase != "loop" or state.step_index != 0:
        errors.append("startup-to-loop transition check failed")
    for _ in LOOP_AXIS:
        state.advance()
    if state.phase != "loop" or state.step_index != 0:
        errors.append("loop repeat transition check failed")
    if errors:
        raise SystemExit("\n".join(errors))
    print("syntax: ok")
    print("axis: ok (startup -> loop, then loop repeats)")


if __name__ == "__main__":
    main()
