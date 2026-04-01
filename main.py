import subprocess
import os
from fastapi import FastAPI
from models import Action, Observation

app = FastAPI()

# Path where we will test the code
TEMP_FILE = "task_run.go"

@app.post("/step")
def step(action: Action):
    # 1. WRITE: Put the AI's code into a real file
    with open(TEMP_FILE, "w") as f:
        f.write(action.new_code)
    
    # 2. RUN: Ask the Go compiler to check the work
    # We use 'go run' to see if it works, or 'go build' to just check syntax
    try:
        result = subprocess.run(
            ["go", "run", TEMP_FILE], 
            capture_output=True, 
            text=True, 
            timeout=15 # Safety Net: 5 second limit
        )
        
        # 3. SCORE: Did it work?
        if result.returncode == 0:
            reward = 1.0
            error_msg = "Success!"
            done = True
        else:
            reward = 0.0
            error_msg = result.stderr # Show the AI the compiler error
            done = False
            
    except subprocess.TimeoutExpired:
        reward = 0.0
        error_msg = "Error: Code execution timed out (Infinite loop?)"
        done = False

    return {
        "reward": reward,
        "done": done,
        "observation": {
            "code": action.new_code,
            "error": error_msg,
            "task_id": "day2_test"
        }
    }