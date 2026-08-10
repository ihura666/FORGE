from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class LicenseInfo:
    key: str
    plan: str
    status: str
    activations: int
    max_activations: int


class LicenseManager:

    def __init__(
        self,
        license_path: Path | None = None,
    ):
        if license_path is None:
            license_path = (
                Path.home()
                / ".forge"
                / "license.json"
            )

        self.license_path = license_path

    def load(self) -> LicenseInfo | None:

        if not self.license_path.exists():
            return None

        try:

            data = json.loads(
                self.license_path.read_text(
                    encoding="utf-8"
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return None

        key = str(
            data.get("key", "")
        ).strip()

        plan = str(
            data.get("plan", "")
        ).strip().lower()

        status = str(
            data.get("status", "")
        ).strip().lower()

        if not key:
            return None

        if plan != "pro":
            return None

        if status != "active":
            return None

        try:
            activations = int(
                data.get("activations", 0)
            )

            max_activations = int(
                data.get("max_activations", 2)
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

        return LicenseInfo(
            key=key,
            plan=plan,
            status=status,
            activations=activations,
            max_activations=max_activations,
        )

    def is_pro(self) -> bool:
        return self.load() is not None

    def mode(self) -> str:

        if self.is_pro():
            return "pro"

        return "free"
