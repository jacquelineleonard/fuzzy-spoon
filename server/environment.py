import subprocess
from pathlib import Path
import json


TASKS_DIR = Path("tasks")


def load_task(task_id):
    task_path = TASKS_DIR / task_id

    with open(task_path / "task.json") as f:
        task = json.load(f)

    with open(task_path / "buggy.go") as f:
        code = f.read()

    with open(task_path / "tests.json") as f:
        tests = json.load(f)

    return task, code, tests


def run_go_code(code: str):
    with open("temp.go", "w") as f:
        f.write(code)

    try:
        result = subprocess.run(
            ["go", "run", "temp.go"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0, result.stdout + result.stderr

    except Exception as e:
        return False, str(e)


def evaluate(task_id: str, action):
    _, broken_code, _ = load_task(task_id)

    reward = 0.0

    # STEP 1: Was original code broken?
    original_success, _ = run_go_code(broken_code)

    if not original_success:
        reward += 0.5

    # STEP 2: Did agent fix it?
    fixed_success, _ = run_go_code(action.fixed_code)

    if fixed_success:
        reward += 0.5
    print("ORIGINAL SUCCESS:", original_success)
    print("FIXED SUCCESS:", fixed_success)
    return reward