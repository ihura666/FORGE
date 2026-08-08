from itertools import product
from typing import Iterator


def exhaustive_candidates(
    alphabet: str,
    length: int,
    start: int = 0,
) -> Iterator[tuple[int, str]]:
    """
    Deterministically traverse a defined search space.

    Yields:
        (position, candidate)
    """

    if not alphabet:
        raise ValueError(
            "alphabet cannot be empty"
        )

    if length < 1:
        raise ValueError(
            "length must be greater than zero"
        )

    if start < 0:
        raise ValueError(
            "start cannot be negative"
        )

    for index, parts in enumerate(
        product(
            alphabet,
            repeat=length,
        )
    ):
        if index < start:
            continue

        yield index, "".join(parts)
