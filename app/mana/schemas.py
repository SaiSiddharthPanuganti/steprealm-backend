from pydantic import BaseModel, Field


class AddStepsRequest(BaseModel):
    step_delta: int = Field(ge=0, le=20000)
