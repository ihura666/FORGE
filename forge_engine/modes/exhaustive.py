from collections.abc import Iterator
from itertools import product

from forge_engine.core.engine import GenerationEngine
from forge_engine.core.result import Candidate


class ExhaustiveEngine(GenerationEngine):

    def generate(
        self,
        start: int = 0,
    ) -> Iterator[Candidate]:

        alphabet = self._alphabet()

        if not alphabet:
            return

        length = self.config.required_length

        if length < 1:
            return

        generated = 0
        position = 0

        for symbols in product(
            alphabet,
            repeat=length,
        ):

            candidate = "".join(symbols)

            if position < start:
                position += 1
                continue

            yield Candidate(
                value=candidate,
                source="exhaustive",
                index=position,
            )

            position += 1
            generated += 1

            if generated >= (
                self.config.max_candidates
            ):
                return

    def _alphabet(self) -> list[str]:

        characters: list[str] = []

        # Preserve keyword characters in the order supplied.
        for keyword in self.config.keywords:

            for character in keyword:

                if character:
                    characters.append(character)

        # Add numbers.
        for number in self.config.numbers:

            for character in number:

                if character:
                    characters.append(character)

        # Add symbols.
        for symbol in self.config.symbols:

            for character in symbol:

                if character:
                    characters.append(character)

        # Remove duplicates while preserving order.
        return list(
            dict.fromkeys(characters)
        )
