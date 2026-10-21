import re
from typing import Optional
from pydantic import BaseModel, field_validator
from src.api.models import SANDBOX_REGEX, ALLOWED_STATES, ALLOWED_TARGET


class RunCreate(BaseModel):
    run_id: str
    sandbox_name: str
    problem_id: str
    state: str
    execution_target: str

    @field_validator("execution_target")
    @classmethod
    def validate_execution_target(cls, v: str) -> str:
        if v != ALLOWED_TARGET:
            raise ValueError(f"execution_target must be exactly '{ALLOWED_TARGET}', got '{v}'")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        if v not in ALLOWED_STATES:
            raise ValueError(f"state must be one of {sorted(ALLOWED_STATES)}, got '{v}'")
        return v

    @field_validator("sandbox_name")
    @classmethod
    def validate_sandbox_name(cls, v: str) -> str:
        if not SANDBOX_REGEX.match(v):
            raise ValueError(
                f"sandbox_name '{v}' is invalid; must start with 'sbx-' followed by 8 or more lowercase alphanumeric chars"
            )
        return v


class RunResponse(BaseModel):
    run_id: str
    sandbox_name: str
    problem_id: str
    state: str
    execution_target: str
    created_at: Optional[str] = None
