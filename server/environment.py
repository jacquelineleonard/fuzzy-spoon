import os
import json
import subprocess
import tempfile

BASE_TASKS_DIR = "tasks"


def load_task(task_id):
    task_path = os.path.join(BASE_TASKS_DIR, task_id)

    with open(os.path.join(task_path, "task.json")) as f:
        task = json.load(f)

    with open(os.path.join(task_path, "buggy.go")) as f:
        code = f.read()

    with open(os.path.join(task_path, "tests.json")) as f:
        tests = json.load(f)

    return task, code, tests


def run_go_code(code: str, timeout=2):
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "main.go")

            with open(file_path, "w") as f:
                f.write(code)

            # Compile
            compile_process = subprocess.run(
                ["go", "build", "main.go"],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )

            if compile_process.returncode != 0:
                return False, compile_process.stderr

            # Run
            try:
                run_process = subprocess.run(
                    ["./main"],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                return True, run_process.stdout.strip()

            except subprocess.TimeoutExpired:
                return False, "timeout"

    except Exception as e:
        return False, str(e)


def evaluate_simple(code: str, tests: dict):
    success, output = run_go_code(code)

    print("RAW:", repr(output))

    if not success:
        return 0.0

    outputs = output.splitlines()
    outputs = [line.strip() for line in outputs if line.strip()]

    expected = [str(x).strip() for x in tests["expected_outputs"]]

    print("OUTPUT:", outputs)
    print("EXPECTED:", expected)

    passed = 0
    total = len(expected)

    for i in range(min(len(outputs), total)):
        if outputs[i] == expected[i]:
            passed += 1

    return passed / total


def evaluate_concurrency(code: str, tests: dict):
    results = []

    for _ in range(3):
        success, output = run_go_code(code)

        if not success:
            return 0.0

        results.append(output)

    # Check consistency
    if len(set(results)) != 1:
        return 0.0

    expected = str(tests["expected_outputs"][0])

    if results[0] == expected:
        return 1.0
    else:
        return 0.5


def evaluate(task_id: str, code: str):
    print("EVALUATE CALLED FOR:", task_id)

    task, _, tests = load_task(task_id)

    if "concurrency" in task_id:
        print("USING CONCURRENCY EVAL")
        return evaluate_concurrency(code, tests)

    print("USING SIMPLE EVAL")
    return evaluate_simple(code, tests)

    

