from collections.abc import Iterator

from forge_engine.core.engine import GenerationEngine
from forge_engine.core.result import Candidate


class SmartEngine(GenerationEngine):

    def generate(
        self,
        start: int = 0,
    ) -> Iterator[Candidate]:

        position = 0

        for keyword in self.config.keywords:

            forms = self._forms(keyword)

            for form in forms:

                candidates = self._expand(
                    form
                )

                for candidate in candidates:

                    if position < start:
                        position += 1
                        continue

                    if len(candidate) != (
                        self.config.required_length
                    ):
                        continue

                    yield Candidate(
                        value=candidate,
                        source="smart",
                        index=position,
                    )

                    position += 1

                    if (
                        position
                        >= self.config.max_candidates
                        + start
                    ):
                        return

    def _forms(
        self,
        keyword: str,
    ) -> list[str]:

        cleaned = (
            keyword
            .strip()
            .lower()
        )

        if not cleaned:
            return []

        forms = [
            cleaned,
            cleaned.capitalize(),
            cleaned.upper(),
            cleaned.title(),
        ]

        return list(
            dict.fromkeys(forms)
        )

    def _expand(
        self,
        form: str,
    ) -> list[str]:

        candidates = [
            form
        ]

        numbers = (
            self.config.numbers
        )

        symbols = (
            self.config.symbols
        )

        remaining = (
            self.config.required_length
            - len(form)
        )

        if remaining < 0:
            return []

        # Exact numeric suffix/prefix.
        if numbers and remaining > 0:

            self._add_numeric_variants(
                candidates,
                form,
                numbers,
                remaining,
            )

        # Exact symbol variants.
        if symbols and remaining > 0:

            self._add_symbol_variants(
                candidates,
                form,
                symbols,
                remaining,
            )

        # Direct candidate.
        if len(form) == (
            self.config.required_length
        ):
            candidates.append(form)

        return list(
            dict.fromkeys(candidates)
        )

    @staticmethod
    def _add_numeric_variants(
        candidates: list[str],
        form: str,
        numbers: list[str],
        remaining: int,
    ) -> None:

        if remaining == 1:

            for number in numbers:
                candidates.append(
                    form + number
                )
                candidates.append(
                    number + form
                )

    @staticmethod
    def _add_symbol_variants(
        candidates: list[str],
        form: str,
        symbols: list[str],
        remaining: int,
    ) -> None:

        if remaining == 1:

            for symbol in symbols:
                candidates.append(
                    form + symbol
                )
                candidates.append(
                    symbol + form
                )
