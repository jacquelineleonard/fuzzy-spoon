import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from models import Action, Observation, StepResult
from server.environment import GoCodeReviewEnv, TASK_ORDER

app = FastAPI(
    title="Go Code Review Environment",
    description="OpenEnv environment for AI agents to review and fix buggy Go code",
    version="1.0.0",
)

# One env instance per task — keeps state isolated
_envs: dict[str, GoCodeReviewEnv] = {
    task_id: GoCodeReviewEnv(task_id=task_id)
    for task_id in TASK_ORDER
}


def get_env(task_id: str) -> GoCodeReviewEnv:
    if task_id not in _envs:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found. Valid: {TASK_ORDER}")
    return _envs[task_id]


@app.get("/")
def root():
    return {"status": "ok", "tasks": TASK_ORDER}


@app.get("/tasks")
def list_tasks():
    return {"tasks": TASK_ORDER}


@app.post("/reset")
def reset(task_id: str = "task1_syntax"):
    env = get_env(task_id)
    obs = env.reset()
    return obs.model_dump()


@app.post("/step")
def step(action: Action, task_id: str = "task1_syntax"):
    env = get_env(task_id)
    try:
        result = env.step(action)
        return result.model_dump()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state")
def state(task_id: str = "task1_syntax"):
    env = get_env(task_id)
    return env.state()


@app.get("/health")
def health():
    return {"status": "healthy"}

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)


if name == "main":
    main()