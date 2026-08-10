from __future__ import annotations

from collections.abc import Iterator
from itertools import product

from forge_engine.core.engine import GenerationEngine
from forge_engine.core.result import Candidate


class SmartEngine(GenerationEngine):

    def generate(
        self,
        start: int = 0,
    ) -> Iterator[Candidate]:

        seen: set[str] = set()
        position = 0
        emitted = 0

        required_length = (
            self.config.required_length
        )

        limit = (
            self.config.max_candidates
        )

        keywords = [
            keyword.strip()
            for keyword in self.config.keywords
            if keyword.strip()
        ]

        numbers = [
            str(number)
            for number in self.config.numbers
            if str(number)
        ]

        symbols = [
            str(symbol)
            for symbol in self.config.symbols
            if str(symbol)
        ]

        # ---------------------------------------------------------
        # Phase 1: direct keyword transformations
        # ---------------------------------------------------------

        forms: list[str] = []

        for keyword in keywords:

            variants = [
                keyword.lower(),
                keyword.capitalize(),
                keyword.upper(),
                keyword.title(),
            ]

            for variant in variants:

                if variant not in forms:
                    forms.append(variant)

        for form in forms:

            if len(form) != required_length:
                continue

            if form in seen:
                continue

            seen.add(form)

            if position < start:
                position += 1
                continue

            yield Candidate(
                value=form,
                source="smart",
                index=position,
            )

            position += 1
            emitted += 1

            if emitted >= limit:
                return

        # ---------------------------------------------------------
        # Phase 2: keyword + number / symbol
        # ---------------------------------------------------------

        modifiers = numbers + symbols

        for form in forms:

            for modifier in modifiers:

                candidates = (
                    form + modifier,
                    modifier + form,
                )

                for candidate in candidates:

                    if len(candidate) != required_length:
                        continue

                    if candidate in seen:
                        continue

                    seen.add(candidate)

                    if position < start:
                        position += 1
                        continue

                    yield Candidate(
                        value=candidate,
                        source="smart",
                        index=position,
                    )

                    position += 1
                    emitted += 1

                    if emitted >= limit:
                        return

        # ---------------------------------------------------------
        # Phase 3: keyword + number + symbol
        # ---------------------------------------------------------

        for form in forms:

            for number in numbers:

                for symbol in symbols:

                    candidates = (
                        form + number + symbol,
                        form + symbol + number,
                        number + form + symbol,
                        symbol + form + number,
                        number + symbol + form,
                        symbol + number + form,
                    )

                    for candidate in candidates:

                        if len(candidate) != required_length:
                            continue

                        if candidate in seen:
                            continue

                        seen.add(candidate)

                        if position < start:
                            position += 1
                            continue

                        yield Candidate(
                            value=candidate,
                            source="smart",
                            index=position,
                        )

                        position += 1
                        emitted += 1

                        if emitted >= limit:
                            return

        # ---------------------------------------------------------
        # Phase 4: combinations of multiple keywords
        # ---------------------------------------------------------

        if len(keywords) >= 2:

            for left in forms:

                for right in forms:

                    if left == right:
                        continue

                    candidate_parts = (
                        left + right,
                        right + left,
                    )

                    for candidate in candidate_parts:

                        if len(candidate) != required_length:
                            continue

                        if candidate in seen:
                            continue

                        seen.add(candidate)

                        if position < start:
                            position += 1
                            continue

                        yield Candidate(
                            value=candidate,
                            source="smart",
                            index=position,
                        )

                        position += 1
                        emitted += 1

                        if emitted >= limit:
                            return

        # ---------------------------------------------------------
        # Phase 5: repeated modifier combinations
        # ---------------------------------------------------------

        modifiers = numbers + symbols

        if modifiers:

            for form in forms:

                remaining = (
                    required_length - len(form)
                )

                if remaining <= 0:
                    continue

                if remaining > 6:
                    continue

                for modifier_tuple in product(
                    modifiers,
                    repeat=remaining,
                ):

                    suffix = "".join(
                        modifier_tuple
                    )

                    candidates = (
                        form + suffix,
                        suffix + form,
                    )

                    for candidate in candidates:

                        if len(candidate) != required_length:
                            continue

                        if candidate in seen:
                            continue

                        seen.add(candidate)

                        if position < start:
                            position += 1
                            continue

                        yield Candidate(
                            value=candidate,
                            source="smart",
                            index=position,
                        )

                        position += 1
                        emitted += 1

                        if emitted >= limit:
                            return
