"""
inference.py — Go Code Review Environment
Runs an LLM agent against all 3 tasks and emits required [START]/[STEP]/[END] logs.
"""

import os
import json
import sys
from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
API_KEY      = os.getenv("HF_TOKEN")     or os.getenv("API_KEY", "")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")
BENCHMARK    = "go-code-review"
MAX_STEPS    = 3
TEMPERATURE  = 0.2

TASKS = ["task1_syntax", "task2_pointer", "task3_concurrency"]

client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

# ── HTTP helpers (no extra deps, use stdlib) ──────────────────────────────────
import urllib.request
import urllib.parse

def _post(path: str, body: dict) -> dict:
    url = ENV_BASE_URL + path
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def _get(path: str) -> dict:
    url = ENV_BASE_URL + path
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())

# ── Prompt ────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert Go code reviewer.
You will be given buggy Go code. Your job is to:
1. Identify ALL bugs (logical, runtime, or design)
2. Return a JSON object with exactly these fields:
   - issues_found: list of strings, one per bug found
   - severity: "low", "medium", or "high"
   - fixed_code: complete fixed Go source code (full file, not a snippet)
   - explanation: brief explanation of each fix

Return ONLY valid JSON. No markdown, no backticks, no extra text."""

def ask_agent(buggy_code: str, description: str) -> dict:
    """Call LLM and parse its JSON response."""
    user_msg = f"Task: {description}\n\nBuggy Go code:\n```go\n{buggy_code}\n```\n\nReturn your review as JSON."
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=TEMPERATURE,
        max_tokens=2000,
    )
    
    raw = response.choices[0].message.content.strip()
    
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    return json.loads(raw.strip())


# ── Main loop ─────────────────────────────────────────────────────────────────
def run_task(task_id: str):
    # Reset env
    obs = _post(f"/reset?task_id={task_id}", {})
    
    print(f"[START] task={task_id} env={BENCHMARK} model={MODEL_NAME}", flush=True)
    
    all_rewards = []
    step_num = 0
    last_error = "null"
    success = False
    final_score = 0.0

    for step_num in range(1, MAX_STEPS + 1):
        # Get agent action
        try:
            agent_json = ask_agent(obs["buggy_code"], obs["description"])
            action = {
                "issues_found": agent_json.get("issues_found", []),
                "severity":     agent_json.get("severity", "medium"),
                "fixed_code":   agent_json.get("fixed_code", ""),
                "explanation":  agent_json.get("explanation", ""),
            }
            last_error = "null"
        except Exception as e:
            last_error = str(e).replace("\n", " ")[:100]
            action = {"issues_found": [], "severity": "low", "fixed_code": "", "explanation": ""}

        # Step env
        result = _post(f"/step?task_id={task_id}", action)
        reward  = result["reward"]["total"]
        done    = result["done"]
        obs     = result["observation"]

        all_rewards.append(reward)
        final_score = reward

        action_str = f"issues={len(action['issues_found'])} compile={'ok' if result['reward']['compile_score']>0 else 'fail'}"
        print(
            f"[STEP] step={step_num} action={action_str} "
            f"reward={reward:.2f} done={'true' if done else 'false'} error={last_error}",
            flush=True
        )

        if done:
            success = reward >= 0.8
            break

    rewards_str = ",".join(f"{r:.2f}" for r in all_rewards)
    print(
        f"[END] success={'true' if success else 'false'} steps={step_num} "
        f"score={final_score:.2f} rewards={rewards_str}",
        flush=True
    )
    print(flush=True)

    return final_score


def main():
    # Quick health check
    try:
        _get("/health")
    except Exception as e:
        print(f"ERROR: Cannot reach environment at {ENV_BASE_URL}: {e}", file=sys.stderr)
        sys.exit(1)

    scores = []
    for task_id in TASKS:
        score = run_task(task_id)
        scores.append(score)

    avg = sum(scores) / len(scores)
    print(f"# Final average score: {avg:.2f}", flush=True)


if __name__ == "__main__":
    main()