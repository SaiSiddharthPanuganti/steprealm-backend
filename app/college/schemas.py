from pydantic import BaseModel, Field, field_validator


class JoinCollegeRequest(BaseModel):
    join_code: str = Field(min_length=3, max_length=64)

    @field_validator("join_code")
    @classmethod
    def normalize_join_code(cls, value: str) -> str:
        return value.strip()
