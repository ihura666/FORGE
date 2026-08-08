from dataclasses import dataclass


@dataclass
class GenerationStats:
    generated: int = 0
    duplicates: int = 0
    rejected: int = 0
    processed: int = 0


@dataclass
class Candidate:
    value: str
    source: str
    index: int
