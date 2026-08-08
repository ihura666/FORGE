from dataclasses import dataclass, asdict
from pathlib import Path
import json
import time


@dataclass
class Checkpoint:
    job_id: str
    mode: str
    position: int = 0
    generated: int = 0
    status: str = "created"
    updated_at: float = 0.0

    def save(self, path: Path) -> None:
        self.updated_at = time.time()

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = path.with_suffix(
            path.suffix + ".tmp"
        )

        temporary.write_text(
            json.dumps(
                asdict(self),
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary.replace(path)

    @classmethod
    def load(cls, path: Path) -> "Checkpoint":
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        return cls(**data)

