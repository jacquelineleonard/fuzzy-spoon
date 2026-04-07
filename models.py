from pydantic import BaseModel, Field
from typing import List


class Observation(BaseModel):
    task_id: str = Field(...)
    code: str = Field(...)
    description: str = Field("")
    score: float = Field(0.0)


class Action(BaseModel):
    issues_found: List[str] = Field(default_factory=list)
    severity: str = Field(default="low")
    fixed_code: str = Field(...)