from dataclasses import dataclass
from enum import Enum


class GenerationMode(str, Enum):
    SMART = "smart"
    SCRAMBLED = "scrambled"
    EXHAUSTIVE = "exhaustive"


class TraversalMode(str, Enum):
    SEQUENTIAL = "sequential"
    PRIORITY = "priority"
    ROTATION = "rotation"
    ALPHABETICAL = "alphabetical"
    RANDOM = "random"


@dataclass
class GenerationConfig:
    mode: GenerationMode
    traversal: TraversalMode
    required_length: int
    max_candidates: int

    keywords: list[str]
    numbers: list[str]
    symbols: list[str]

    def validate(self) -> None:
        if self.required_length < 1:
            raise ValueError(
                "required_length must be greater than zero"
            )

        if self.max_candidates < 1:
            raise ValueError(
                "max_candidates must be greater than zero"
            )

        if not self.keywords:
            raise ValueError(
                "At least one keyword is required"
            )
