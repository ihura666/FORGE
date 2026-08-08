from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class JobStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class GenerationJob:
    """
    Represents a FORGE generation job.

    Supports both the current pipeline constructor:

        GenerationJob(
            job_id="test-001",
            config=config,
            output_path=output,
            checkpoint_path=checkpoint,
        )

    and the legacy JobManager constructor:

        GenerationJob(
            mode="exhaustive",
            traversal="sequential",
            required_length=8,
            max_candidates=1000,
        )
    """

    # Primary identity
    job_id: str

    # New pipeline configuration
    config: Any = None

    # File locations used by the pipeline
    output_path: Optional[Path] = None
    checkpoint_path: Optional[Path] = None

    # Legacy / compatibility configuration
    mode: str = "exhaustive"
    traversal: str = "sequential"
    required_length: int = 8
    max_candidates: int = 1000

    # Generation inputs
    keywords: list[str] = field(default_factory=list)
    numbers: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)

    # Output
    output_file: str = "output.txt"

    # Runtime state
    status: JobStatus = JobStatus.CREATED

    # Checkpoint state
    position: int = 0
    generated: int = 0

    # Compatibility aliases used by older code
    current_index: int = 0
    total_generated: int = 0

    # Metadata
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Normalize configuration after construction.

        If a GenerationConfig object is supplied, copy its values into
        the compatibility fields so both the new and old APIs remain
        synchronized.
        """

        # Normalize paths
        if self.output_path is not None:
            self.output_path = Path(self.output_path)

        if self.checkpoint_path is not None:
            self.checkpoint_path = Path(self.checkpoint_path)

        # Pull values from GenerationConfig when available.
        if self.config is not None:
            self.mode = self._get_config_value(
                "mode",
                self.mode,
            )

            self.traversal = self._get_config_value(
                "traversal",
                self.traversal,
            )

            self.required_length = self._get_config_value(
                "required_length",
                self.required_length,
            )

            self.max_candidates = self._get_config_value(
                "max_candidates",
                self.max_candidates,
            )

            self.keywords = list(
                self._get_config_value(
                    "keywords",
                    self.keywords,
                )
                or []
            )

            self.numbers = list(
                self._get_config_value(
                    "numbers",
                    self.numbers,
                )
                or []
            )

            self.symbols = list(
                self._get_config_value(
                    "symbols",
                    self.symbols,
                )
                or []
            )

        # Normalize enum-like values to strings where appropriate.
        if isinstance(self.mode, Enum):
            self.mode = self.mode.value

        if isinstance(self.traversal, Enum):
            self.traversal = self.traversal.value

        self.mode = str(self.mode)
        self.traversal = str(self.traversal)

        # Keep aliases synchronized at construction.
        self.current_index = self.position
        self.total_generated = self.generated

        # Derive output filename if an output path exists.
        if self.output_path is not None:
            self.output_file = self.output_path.name

        self.updated_at = time.time()

    def _get_config_value(
        self,
        name: str,
        default: Any,
    ) -> Any:
        """
        Read a value from either a dataclass/object-style config or
        dictionary-style config.
        """

        if isinstance(self.config, dict):
            return self.config.get(name, default)

        return getattr(
            self.config,
            name,
            default,
        )

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def set_position(self, position: int) -> None:
        """Update the current generation position."""

        if position < 0:
            raise ValueError(
                "position cannot be negative"
            )

        self.position = int(position)
        self.current_index = self.position
        self.updated_at = time.time()

    def set_generated(self, generated: int) -> None:
        """Update the number of generated candidates."""

        if generated < 0:
            raise ValueError(
                "generated cannot be negative"
            )

        self.generated = int(generated)
        self.total_generated = self.generated
        self.updated_at = time.time()

    def update_checkpoint(
        self,
        position: Optional[int] = None,
        generated: Optional[int] = None,
    ) -> None:
        """
        Update checkpoint information atomically.
        """

        if position is not None:
            self.set_position(position)

        if generated is not None:
            self.set_generated(generated)

        self.updated_at = time.time()

    # ------------------------------------------------------------------
    # Job lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Mark the job as running."""

        if self.status in {
            JobStatus.COMPLETED,
            JobStatus.CANCELLED,
        }:
            raise RuntimeError(
                f"Cannot start job in state: {self.status.value}"
            )

        self.status = JobStatus.RUNNING
        self.updated_at = time.time()

    def pause(
        self,
        position: Optional[int] = None,
        generated: Optional[int] = None,
    ) -> None:
        """Pause the job and optionally save checkpoint state."""

        self.update_checkpoint(
            position=position,
            generated=generated,
        )

        self.status = JobStatus.PAUSED
        self.updated_at = time.time()

    def resume(self) -> None:
        """Resume a paused job."""

        if self.status != JobStatus.PAUSED:
            raise RuntimeError(
                "Only paused jobs can be resumed"
            )

        self.status = JobStatus.RUNNING
        self.updated_at = time.time()

    def complete(self) -> None:
        """Mark the job as completed."""

        self.status = JobStatus.COMPLETED
        self.updated_at = time.time()

    def fail(self) -> None:
        """Mark the job as failed."""

        self.status = JobStatus.FAILED
        self.updated_at = time.time()

    def cancel(self) -> None:
        """Cancel the job."""

        self.status = JobStatus.CANCELLED
        self.updated_at = time.time()

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the job into a JSON-compatible dictionary.
        """

        config_data = None

        if self.config is not None:
            if hasattr(self.config, "to_dict"):
                config_data = self.config.to_dict()

            elif hasattr(self.config, "__dict__"):
                config_data = dict(
                    self.config.__dict__
                )

            elif isinstance(self.config, dict):
                config_data = dict(self.config)

        return {
            "job_id": self.job_id,

            "config": config_data,

            "output_path": (
                str(self.output_path)
                if self.output_path is not None
                else None
            ),

            "checkpoint_path": (
                str(self.checkpoint_path)
                if self.checkpoint_path is not None
                else None
            ),

            "mode": self.mode,
            "traversal": self.traversal,
            "required_length": self.required_length,
            "max_candidates": self.max_candidates,

            "keywords": list(self.keywords),
            "numbers": list(self.numbers),
            "symbols": list(self.symbols),

            "output_file": self.output_file,

            "status": self.status.value,

            "position": self.position,
            "generated": self.generated,

            "current_index": self.current_index,
            "total_generated": self.total_generated,

            "created_at": self.created_at,
            "updated_at": self.updated_at,

            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        config: Any = None,
    ) -> "GenerationJob":
        """
        Restore a GenerationJob from persisted checkpoint data.
        """

        if not isinstance(data, dict):
            raise TypeError(
                "data must be a dictionary"
            )

        status_value = data.get(
            "status",
            JobStatus.CREATED.value,
        )

        try:
            status = JobStatus(status_value)
        except ValueError:
            status = JobStatus.CREATED

        job = cls(
            job_id=data.get(
                "job_id",
                "F-unknown",
            ),

            config=config,

            output_path=(
                Path(data["output_path"])
                if data.get("output_path")
                else None
            ),

            checkpoint_path=(
                Path(data["checkpoint_path"])
                if data.get("checkpoint_path")
                else None
            ),

            mode=data.get(
                "mode",
                "exhaustive",
            ),

            traversal=data.get(
                "traversal",
                "sequential",
            ),

            required_length=int(
                data.get(
                    "required_length",
                    8,
                )
            ),

            max_candidates=int(
                data.get(
                    "max_candidates",
                    1000,
                )
            ),

            keywords=list(
                data.get(
                    "keywords",
                    [],
                )
            ),

            numbers=list(
                data.get(
                    "numbers",
                    [],
                )
            ),

            symbols=list(
                data.get(
                    "symbols",
                    [],
                )
            ),

            output_file=data.get(
                "output_file",
                "output.txt",
            ),

            status=status,

            position=int(
                data.get(
                    "position",
                    data.get(
                        "current_index",
                        0,
                    ),
                )
            ),

            generated=int(
                data.get(
                    "generated",
                    data.get(
                        "total_generated",
                        0,
                    ),
                )
            ),

            created_at=float(
                data.get(
                    "created_at",
                    time.time(),
                )
            ),

            updated_at=float(
                data.get(
                    "updated_at",
                    time.time(),
                )
            ),

            metadata=dict(
                data.get(
                    "metadata",
                    {},
                )
            ),
        )

        return job
