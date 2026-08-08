from abc import ABC, abstractmethod
from collections.abc import Iterator

from forge_engine.core.config import GenerationConfig
from forge_engine.core.result import Candidate


class GenerationEngine(ABC):

    def __init__(
        self,
        config: GenerationConfig,
    ):
        self.config = config
        self.config.validate()

    @abstractmethod
    def generate(
        self,
        start: int = 0,
    ) -> Iterator[Candidate]:
        """
        Generate candidates starting from a deterministic position.
        """
        raise NotImplementedError
