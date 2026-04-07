---
title: Go Code Review OpenEnv
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
sdk_version: "1.0"
app_file: server/app.py
pinned: false
---
# Go Code Review OpenEnv

An OpenEnv-compatible environment where AI agents review and fix buggy Go code across multiple tasks of increasing complexity.

---

## Overview

This project implements a reinforcement learning-style environment for evaluating AI agents on software engineering tasks. The agent is given buggy Go code and must:

* Identify issues in the code
* Provide a corrected version
* Improve performance across iterative steps

The system evaluates the agent using structured rewards based on:

* Bug identification accuracy
* Compilation success
* Test case correctness

---

## Features

* OpenEnv-compliant API (`/reset`, `/step`, `/state`)
* Multi-task evaluation (3 tasks)
* Structured reward system (0.0 – 1.0)
* Robust inference pipeline with fallback handling
* Dockerized for deployment (Hugging Face Spaces compatible)

---

## Tasks

### Task 1: Syntax & Logic Errors

* Fix incorrect logical conditions
* Correct discount calculations

### Task 2: Nil Pointer Handling

* Detect and fix nil pointer dereferences
* Ensure safe pointer usage

### Task 3: Concurrency & Pagination Bugs

* Fix slice modification issues
* Handle pagination correctly
* Prevent out-of-bounds errors

---

## Project Structure

```
fuzzy-spoon/
│
├── server/
│   ├── app.py              # FastAPI endpoints
│   ├── environment.py      # OpenEnv environment logic
│   ├── grader.py           # Evaluation logic
│   └── tasks/              # Task definitions
│
├── tasks/
│   ├── index.json
│   ├── task1_syntax/
│   ├── task2_pointer/
│   └── task3_concurrency/
│
├── inference.py            # Agent + evaluation loop
├── openenv.yaml            # OpenEnv specification
├── Dockerfile              # Deployment config
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd fuzzy-spoon
```

---

### 2. Install dependencies

```bash
pip install fastapi uvicorn openai python-dotenv
```

---

### 3. Set environment variables

```bash
export API_KEY=<your_api_key>
export API_BASE_URL=https://api.cerebras.ai/v1
export MODEL_NAME=llama3.1-8b
export ENV_BASE_URL=http://127.0.0.1:7860
```

---

## Running the Environment

### Start FastAPI server

```bash
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

---

### Test API

Open:

```
http://127.0.0.1:7860/docs
```

---

## Running Inference

```bash
python3 inference.py
```

---

## Output Format

The system logs execution in structured format:

```
[START] task=... env=... model=...
[STEP] step=... action=... reward=... done=...
[END] success=... steps=... score=...
```

---

## Reward System

| Component     | Range   | Description                |
| ------------- | ------- | -------------------------- |
| Review Score  | 0.0–0.4 | Bug identification         |
| Compile Score | 0.0–0.2 | Code compiles successfully |
| Test Score    | 0.0–0.4 | Test cases passed          |

Total reward ∈ [0.0, 1.0]

---

## Docker Deployment

Build and run:

```bash
docker build -t go-code-review .
docker run -p 7860:7860 go-code-review
```

---

## OpenEnv Compliance

This project satisfies:

* `/reset`, `/step`, `/state` endpoints
* Typed observation/action schema
* Multi-step episode handling
* Reward normalization (0–1)
* Docker build compatibility

---

## Environment Variables

| Variable     | Description        |
| ------------ | ------------------ |
| API_KEY      | LLM API key        |
| API_BASE_URL | LLM endpoint       |
| MODEL_NAME   | Model identifier   |
| ENV_BASE_URL | OpenEnv server URL |

---

## Notes

* Fallback logic ensures stable execution even if LLM output is invalid
* Designed to run within 20 minutes on limited compute (2 vCPU, 8GB RAM)
* Compatible with Hugging Face Spaces evaluation pipeline

---
