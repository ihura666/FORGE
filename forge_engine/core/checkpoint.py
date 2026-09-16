from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Checkpoint:
    version: int
    output: str
    mode: str
    traversal: str
    lengths: list[int]
    current_length_index: int
    current_position: int
    generated: int
    limit: int
    keywords: list[str]
    numbers: list[str]
    symbols: list[str]
    completed: bool = False

    @property
    def current_length(self) -> int | None:
        if self.current_length_index >= len(self.lengths):
            return None

        return self.lengths[self.current_length_index]


def checkpoint_path(output: Path) -> Path:
    return Path(f"{output}.forge-state")


def save_checkpoint(
    path: Path,
    checkpoint: Checkpoint,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
        text=True,
    )

    try:

        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
        ) as handle:

            json.dump(
                asdict(checkpoint),
                handle,
                indent=2,
                sort_keys=True,
            )

            handle.write("\n")

            handle.flush()
            os.fsync(handle.fileno())

        os.replace(
            temporary,
            path,
        )

    except Exception:

        try:
            os.unlink(
                temporary
            )
        except FileNotFoundError:
            pass

        raise


def load_checkpoint(
    path: Path,
) -> Checkpoint:

    if not path.exists():

        raise ValueError(
            f"Resume state not found: {path}"
        )

    try:

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        # Checkpoints created before the exact-position
        # resume implementation did not contain current_position.
        # Treat their generated count as the position so that
        # completed/legacy checkpoints remain readable.
        if "current_position" not in data:

            data["current_position"] = int(
                data.get(
                    "generated",
                    0,
                )
            )

        if "version" not in data:

            data["version"] = 1

        return Checkpoint(
            **data
        )

    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:

        raise ValueError(
            f"Invalid resume state: {path}"
        ) from exc
