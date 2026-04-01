from pydantic import BaseModel, Field

class Observation(BaseModel):
    code: str = Field(..., description="The broken Go code")
    error: str = Field(..., description="The compiler error message")
    task_id: str

class Action(BaseModel):
    new_code: str = Field(..., description="The full fixed code from the AI")

class Reward(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    done: bool