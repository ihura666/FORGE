from dataclasses import dataclass
from enum import Enum
import uuid


class JobStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    job_id: str
    mode: str
    status: JobStatus = JobStatus.CREATED
    position: int = 0
    generated: int = 0

    @classmethod
    def create(cls, mode: str) -> "Job":
        return cls(
            job_id=f"F-{uuid.uuid4().hex[:8].upper()}",
            mode=mode,
        )
