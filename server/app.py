from fastapi import FastAPI
from models import Action
from server.environment import evaluate, load_task
import json

app = FastAPI()

with open("tasks/index.json") as f:
    TASKS = json.load(f)

current_task_index = 0


@app.post("/reset")
def reset():
    global current_task_index

    current_task_index = (current_task_index + 1) % len(TASKS)
    task_id = TASKS[current_task_index]

    task, code, _ = load_task(task_id)

    return {
        "observation": {
            "task_id": task_id,
            "description": task["description"],
            "code": code
        },
        "reward": 0.0,
        "done": False
    }


@app.post("/step")
def step(action: Action):
    global current_task_index

    task_id = TASKS[current_task_index]

    score = evaluate(task_id, action)

    return {
        "reward": score,
        "done": True,
        "observation": {
            "task_id": task_id,
            "code": action.fixed_code,
            "score": score
        }
    }


@app.get("/state")
def state():
    return {
        "task_id": TASKS[current_task_index]
    }