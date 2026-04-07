import json
import os
from models import Action, Observation, Reward, StepResult
from server.grader import evaluate, load_task

TASKS_DIR = os.path.join(os.path.dirname(__file__), "tasks")
TASK_ORDER = ["task1_syntax", "task2_pointer", "task3_concurrency"]
MAX_STEPS = 3


class GoCodeReviewEnv:
    """
    OpenEnv environment: Go Code Review
    
    The agent receives buggy Go code, must:
      1. Identify what bugs exist (review)
      2. Submit fixed code (rewrite)
    
    Scored on: bug identification + compilation + test passage
    """

    def __init__(self, task_id: str = "task1_syntax"):
        self.task_id = task_id
        self._step_count = 0
        self._done = False
        self._last_reward: Reward | None = None
        self._meta = None
        self._buggy_code = None

    def reset(self) -> Observation:
        """Start a fresh episode for the current task."""
        self._step_count = 0
        self._done = False
        self._last_reward = None

        self._meta, self._buggy_code = load_task(self.task_id)

        return Observation(
            task_id=self.task_id,
            description=self._meta["description"],
            difficulty=self._meta["difficulty"],
            buggy_code=self._buggy_code,
            step=0,
            max_steps=MAX_STEPS,
            last_reward=None,
            done=False,
        )

    def step(self, action: Action) -> StepResult:
        """
        Agent submits an action (issues_found + fixed_code).
        Returns observation, reward, done, info.
        """
        if self._done:
            raise RuntimeError("Episode is done. Call reset() first.")

        self._step_count += 1
        reward = evaluate(self.task_id, action)
        self._last_reward = reward

        # Episode ends if: agent got full score, or max steps reached
        done = (reward.total >= 1.0) or (self._step_count >= MAX_STEPS)
        self._done = done

        obs = Observation(
            task_id=self.task_id,
            description=self._meta["description"],
            difficulty=self._meta["difficulty"],
            buggy_code=self._buggy_code,
            step=self._step_count,
            max_steps=MAX_STEPS,
            last_reward=reward.total,
            done=done,
        )

        return StepResult(
            observation=obs,
            reward=reward,
            done=done,
            info={
                "review_score": reward.review_score,
                "compile_score": reward.compile_score,
                "test_score": reward.test_score,
                "compile_error": reward.compile_error,
                "issues_matched": reward.issues_matched,
                "tests_passed": reward.tests_passed,
            }
        )

    def state(self) -> dict:
        """Return current environment state (for debugging/logging)."""
        return {
            "task_id": self.task_id,
            "step": self._step_count,
            "done": self._done,
            "last_reward": self._last_reward.total if self._last_reward else None,
        }