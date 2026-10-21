import re
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

SANDBOX_REGEX = re.compile(r"^sbx-[a-z0-9]{8,}$")
ALLOWED_STATES = {"created", "ready", "running", "succeeded", "failed", "deleted"}
ALLOWED_TARGET = "celesto_sandbox"


class RunModel(Base):
    __tablename__ = "runs"

    run_id = Column(String(255), primary_key=True, index=True)
    sandbox_name = Column(String(255), nullable=False)
    problem_id = Column(String(255), nullable=False)
    state = Column(String(50), nullable=False)
    execution_target = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "run_id": self.run_id,
            "sandbox_name": self.sandbox_name,
            "problem_id": self.problem_id,
            "state": self.state,
            "execution_target": self.execution_target,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
