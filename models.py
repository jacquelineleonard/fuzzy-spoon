from pydantic import BaseModel, Field
from typing import Optional


class Action(BaseModel):
    """What the agent submits per step."""

    # Review part — agent must identify the bugs
    issues_found: list[str] = Field(
        description="List of bugs the agent identified. Each item is a plain English description.",
        example=["|| should be && in isEligible", "applyDiscount multiplies by 0.20 instead of 0.80"]
    )
    severity: str = Field(
        description="Overall severity: 'low', 'medium', or 'high'",
        example="high"
    )

    # Rewrite part — agent submits fixed code
    fixed_code: str = Field(
        description="Complete fixed Go source code. Must be a full runnable file.",
        example="package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"fixed\") }"
    )

    # Optional explanation
    explanation: Optional[str] = Field(
        default=None,
        description="Optional: agent's reasoning about what was wrong and why the fix works."
    )


class Observation(BaseModel):
    """What the agent sees at each step."""

    task_id: str = Field(description="Current task identifier")
    description: str = Field(description="Human-readable task description")
    difficulty: str = Field(description="easy | medium | hard")
    buggy_code: str = Field(description="The Go source code that needs to be reviewed and fixed")
    step: int = Field(description="Current step number (starts at 1)")
    max_steps: int = Field(default=3, description="Max steps allowed per episode")
    last_reward: Optional[float] = Field(default=None, description="Reward from previous step, if any")
    done: bool = Field(default=False, description="Whether the episode is complete")


class Reward(BaseModel):
    """Breakdown of how the reward was calculated."""

    total: float = Field(description="Total reward between 0.0 and 1.0")

    # Sub-scores
    review_score: float = Field(description="0.0-0.4: how well agent identified the bugs")
    compile_score: float = Field(description="0.0-0.2: whether fixed code compiles")
    test_score: float = Field(description="0.0-0.4: how many test cases the fixed code passes")

    # Details
    issues_matched: int = Field(description="Number of expected keywords matched in agent's issues_found")
    issues_expected: int = Field(description="Total expected keywords for this task")
    tests_passed: int = Field(description="Number of test cases passed")
    tests_total: int = Field(description="Total number of test cases")
    compile_error: Optional[str] = Field(default=None, description="Compiler error if compilation failed")


class StepResult(BaseModel):
    """Full result returned from step()."""

    observation: Observation
    reward: Reward
    done: bool
    info: dict = Field(default_factory=dict)