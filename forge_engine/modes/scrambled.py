from collections.abc import Iterator
from itertools import permutations

from forge_engine.core.engine import GenerationEngine
from forge_engine.core.result import Candidate


class ScrambledEngine(GenerationEngine):

    def generate(
        self,
        start: int = 0,
    ) -> Iterator[Candidate]:

        position = 0

        for keyword in self.config.keywords:

            if not keyword:
                continue

            length = (
                self.config.required_length
            )

            if length > len(keyword):
                continue

            seen = set()

            for permutation in permutations(
                keyword,
                length,
            ):

                candidate = "".join(
                    permutation
                )

                if candidate in seen:
                    continue

                seen.add(candidate)

                if position < start:
                    position += 1
                    continue

                yield Candidate(
                    value=candidate,
                    source="scrambled",
                    index=position,
                )

                position += 1

                if (
                    position
                    >= self.config.max_candidates
                    + start
                ):
                    return
