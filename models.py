from pydantic import BaseModel, Field


class Observation(BaseModel):
    task_id: str = Field(..., description="Current task ID")
    code: str = Field(..., description="Buggy or submitted Go code")
    description: str = Field("", description="Task description")
    score: float = Field(0.0, description="Score after evaluation")


class Action(BaseModel):
    new_code: str = Field(..., description="Full corrected Go code from agent")