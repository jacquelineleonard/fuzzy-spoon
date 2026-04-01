## Three well defined tasks:

1. Check Syntax + Basic Logic : like a missing }
2. Runtime Bug - nil pointer panic
3. Concurrency Issue - race condition

## Universal Grading Template

```python
If compile fails → 0.0

Else:
    run tests

    passed_tests = X
    total_tests = N

    score = X / N
```

### Concurrency Task

```python
run program multiple times

if outputs vary → 0.0
if consistent but wrong → 0.5
if correct → 1.0
```

## Task Data Structure

```python
tasks = [
{
"id": "easy_1",
"description": "...",
"buggy_code": "...",
"tests": [...],
"expected_outputs": [...]
}
]
```

## What the Grader does

1. Take fixed_code
2. Combine with test runner
3. Compile using : *go build*
4. Run program
5. Compare outputs with expected_outputs

## Observation Format

```python
observation = {
"task_id": task["id"],
"description": task["description"],
"code": task["buggy_code"]
}
```

## Action Format

```python
action = {
"fixed_code": "corrected Go code"
}
```