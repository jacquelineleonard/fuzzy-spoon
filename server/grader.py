import subprocess
import tempfile
import os
import json
import re
from models import Action, Reward

TASKS_DIR = os.path.join(os.path.dirname(__file__), "tasks")


def load_task(task_id: str):
    """Load task metadata and buggy code."""
    task_dir = os.path.join(TASKS_DIR, task_id)
    with open(os.path.join(task_dir, "task.json")) as f:
        meta = json.load(f)
    with open(os.path.join(task_dir, "buggy.go")) as f:
        buggy_code = f.read()
    return meta, buggy_code


def compile_go(code: str) -> tuple[bool, str]:
    """
    Write code to a temp file and try to compile it.
    Returns (success, error_message).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        go_file = os.path.join(tmpdir, "main.go")
        with open(go_file, "w") as f:
            f.write(code)
        try:
            result = subprocess.run(
                ["go", "build", "-o", os.path.join(tmpdir, "out"), go_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, ""
            return False, result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "compilation timed out"
        except FileNotFoundError:
            return False, "go compiler not found"


def run_go(code: str, timeout: int = 5) -> tuple[bool, str]:
    """
    Compile and run Go code.
    Returns (success, stdout_output).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        go_file = os.path.join(tmpdir, "main.go")
        binary = os.path.join(tmpdir, "out")
        with open(go_file, "w") as f:
            f.write(code)
        try:
            build = subprocess.run(
                ["go", "build", "-o", binary, go_file],
                capture_output=True, text=True, timeout=10
            )
            if build.returncode != 0:
                return False, build.stderr.strip()

            run = subprocess.run(
                [binary],
                capture_output=True, text=True, timeout=timeout
            )
            if run.returncode != 0:
                return False, run.stderr.strip()
            return True, run.stdout.strip()

        except subprocess.TimeoutExpired:
            return False, "runtime timeout"
        except Exception as e:
            return False, str(e)


def score_review(action: Action, meta: dict) -> tuple[float, int, int]:
    """
    Score how well the agent identified bugs.
    Checks if expected_keywords appear in agent's issues_found list.
    Returns (score 0.0-1.0, matched_count, total_count).
    """
    keywords = meta.get("expected_keywords", [])
    if not keywords:
        return 0.4, 0, 0

    all_issues_text = " ".join(action.issues_found).lower()
    if action.explanation:
        all_issues_text += " " + action.explanation.lower()

    matched = sum(
        1 for kw in keywords
        if kw.lower() in all_issues_text
    )

    # Also check minimum number of issues found
    min_issues = meta.get("expected_issues_min", 1)
    found_enough = len(action.issues_found) >= min_issues

    ratio = matched / len(keywords)
    if not found_enough:
        ratio *= 0.7  # penalty for not finding enough distinct issues

    return min(ratio, 1.0), matched, len(keywords)


def run_task1_tests(fixed_code: str, meta: dict) -> tuple[float, int, int]:
    """
    Task 1: inject test calls and check output.
    Tests isEligible and applyDiscount with specific args.
    """
    test_cases = meta.get("test_cases", [])
    if not test_cases:
        return 0.0, 0, 0

    passed = 0

    for tc in test_cases:
        fn = tc["function"]
        args = tc["args"]
        expected = tc["expected"]

        if fn == "isEligible":
            test_main = f"""
func main() {{
    result := isEligible({args[0]}, {args[1]})
    if result == {str(expected).lower()} {{
        fmt.Println("PASS")
    }} else {{
        fmt.Println("FAIL")
    }}
}}
"""
        elif fn == "applyDiscount":
            test_main = f"""
func main() {{
    result := applyDiscount({args[0]}, {str(args[1]).lower()})
    diff := result - {expected}
    if diff < 0 {{ diff = -diff }}
    if diff < 0.01 {{
        fmt.Println("PASS")
    }} else {{
        fmt.Println("FAIL")
    }}
}}
"""
        else:
            continue

        # Replace main() in fixed code with our test main
        test_code = re.sub(r'func main\(\).*', '', fixed_code, flags=re.DOTALL)
        test_code = test_code.strip() + "\n" + test_main

        success, output = run_go(test_code)
        if success and "PASS" in output:
            passed += 1

    total = len(test_cases)
    return passed / total if total > 0 else 0.0, passed, total


def run_task2_tests(fixed_code: str, meta: dict) -> tuple[float, int, int]:
    """
    Task 2: test that nil pointer cases don't panic.
    Injects orders with bad UserIDs and checks for graceful handling.
    """
    test_cases = meta.get("test_cases", [])
    passed = 0

    for tc in test_cases:
        user_id = tc["trigger_user_id"]
        expected_contains = tc.get("expected_output_contains", "unknown")

        test_main = f"""
func main() {{
    users := []User{{
        {{ID: 1, Name: "Alice", Email: "alice@example.com"}},
        {{ID: 2, Name: "Bob",   Email: "bob@example.com"}},
    }}
    orders := []Order{{
        {{ID: 101, UserID: {user_id}, Amount: 50.0}},
    }}
    processOrders(orders, users)
}}
"""
        test_code = re.sub(r'func main\(\).*', '', fixed_code, flags=re.DOTALL)
        test_code = test_code.strip() + "\n" + test_main

        success, output = run_go(test_code)
        # Must not panic AND output should contain expected string
        if success and expected_contains.lower() in output.lower():
            passed += 1
        elif success and user_id in [1, 2]:
            # Valid user — just needs to not panic
            passed += 1

    total = len(test_cases)
    return passed / total if total > 0 else 0.0, passed, total


def run_task3_tests(fixed_code: str, meta: dict) -> tuple[float, int, int]:
    """
    Task 3: test pagination + filter correctness with edge cases.
    """
    test_cases = meta.get("test_cases", [])
    passed = 0

    products_setup = """
    products := []Product{
        {ID: 1, Name: "Laptop",     Price: 999.99, Stock: 5},
        {ID: 2, Name: "Mouse",      Price: 29.99,  Stock: 0},
        {ID: 3, Name: "Keyboard",   Price: 79.99,  Stock: 3},
        {ID: 4, Name: "Monitor",    Price: 399.99,  Stock: 0},
        {ID: 5, Name: "Headphones", Price: 149.99, Stock: 2},
        {ID: 6, Name: "Webcam",     Price: 89.99,  Stock: 0},
    }
"""

    for tc in test_cases:
        desc = tc.get("description", "")

        if "filterInStock" in desc:
            # Test filter correctness with adjacent zeros
            test_main = """
func main() {
    products := []Product{
        {ID: 1, Price: 10, Stock: 0},
        {ID: 2, Price: 20, Stock: 0},
        {ID: 3, Price: 30, Stock: 5},
        {ID: 4, Price: 40, Stock: 0},
        {ID: 5, Price: 50, Stock: 3},
    }
    result := filterInStock(products)
    fmt.Println(len(result))
}
"""
            expected_count = tc.get("expected_in_stock_count", 2)
            test_code = re.sub(r'func main\(\).*', '', fixed_code, flags=re.DOTALL)
            test_code = test_code.strip() + "\n" + test_main
            success, output = run_go(test_code)
            if success and str(expected_count) in output:
                passed += 1

        else:
            page = tc.get("page", 1)
            page_size = tc.get("page_size", 2)
            expected_count = tc.get("expected_count", 0)
            expected_first = tc.get("expected_first_name", "")

            test_main = f"""
func main() {{
{products_setup}
    result := getTopProducts(products, {page}, {page_size})
    fmt.Println(len(result))
    if len(result) > 0 {{
        fmt.Println(result[0].Name)
    }}
}}
"""
            test_code = re.sub(r'func main\(\).*', '', fixed_code, flags=re.DOTALL)
            test_code = test_code.strip() + "\n" + test_main
            success, output = run_go(test_code)

            if not success:
                # panicked — only pass if expected_count == 0 and page is out of range
                if expected_count == 0 and page == 99:
                    passed += 1
                continue

            lines = output.strip().split("\n")
            count_ok = lines[0].strip() == str(expected_count) if lines else False
            name_ok = (not expected_first) or (len(lines) > 1 and expected_first in lines[1])

            if count_ok and name_ok:
                passed += 1

    total = len(test_cases)
    return passed / total if total > 0 else 0.0, passed, total


TASK_TEST_RUNNERS = {
    "task1_syntax": run_task1_tests,
    "task2_pointer": run_task2_tests,
    "task3_concurrency": run_task3_tests,
}


def evaluate(task_id: str, action: Action) -> Reward:
    """
    Master grader. Returns a full Reward breakdown.

    Scoring:
      0.4 — review: agent correctly identified the bugs
      0.2 — compile: fixed code compiles
      0.4 — tests:  fixed code passes test cases
    """
    meta, _ = load_task(task_id)

    # 1. Score the review (bug identification)
    review_ratio, matched, total_kw = score_review(action, meta)
    review_score = round(0.4 * review_ratio, 3)

    # 2. Score compilation
    compiles, compile_error = compile_go(action.fixed_code)
    compile_score = 0.2 if compiles else 0.0

    # 3. Score test cases (only if it compiled)
    if compiles and task_id in TASK_TEST_RUNNERS:
        test_ratio, tests_passed, tests_total = TASK_TEST_RUNNERS[task_id](action.fixed_code, meta)
        test_score = round(0.4 * test_ratio, 3)
    else:
        test_score = 0.0
        tests_passed = 0
        tests_total = len(meta.get("test_cases", []))

    total = round(review_score + compile_score + test_score, 3)
    total = min(total, 1.0)

    return Reward(
        total=total,
        review_score=review_score,
        compile_score=compile_score,
        test_score=test_score,
        issues_matched=matched,
        issues_expected=total_kw,
        tests_passed=tests_passed,
        tests_total=tests_total,
        compile_error=compile_error if not compiles else None,
    )