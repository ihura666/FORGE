from collections.abc import Iterator
from itertools import product

from forge_engine.core.engine import GenerationEngine
from forge_engine.core.result import Candidate


class ExhaustiveEngine(GenerationEngine):

    def generate(
        self,
        start: int = 0,
    ) -> Iterator[Candidate]:

        position = 0

        alphabet = self._alphabet()

        if not alphabet:
            return

        length = self.config.required_length

        if length < 1:
            return

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

            if (
                position
                >= start
                + self.config.max_candidates
            ):
                return

    def _alphabet(self) -> list[str]:

        alphabet = []

        # Keywords are character pools.
        #
        # Example:
        #
        # ["ab"]
        #
        # becomes:
        #
        # ["a", "b"]
        #
        for keyword in self.config.keywords:

            for character in keyword:

                if character:
                    alphabet.append(
                        character
                    )

        # Numbers and symbols are also
        # individual alphabet elements.
        for number in self.config.numbers:

            for character in number:

                if character:
                    alphabet.append(
                        character
                    )

        for symbol in self.config.symbols:

            for character in symbol:

                if character:
                    alphabet.append(
                        character
                    )

        # Remove duplicates while
        # preserving insertion order.
        return list(
            dict.fromkeys(
                alphabet
            )
        )
