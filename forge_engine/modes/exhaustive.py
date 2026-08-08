from typing import Iterator


def search_space_size(
    alphabet: str,
    length: int,
) -> int:
    """
    Return the total number of candidates in the search space.
    """

    if not alphabet:
        raise ValueError("alphabet cannot be empty")

    if length < 1:
        raise ValueError(
            "length must be greater than zero"
        )

    return len(alphabet) ** length


def candidate_from_index(
    alphabet: str,
    length: int,
    index: int,
) -> str:
    """
    Convert a numeric position directly into a candidate.

    This allows exhaustive jobs to resume without replaying
    candidates that were already processed.
    """

    if not alphabet:
        raise ValueError("alphabet cannot be empty")

    if length < 1:
        raise ValueError(
            "length must be greater than zero"
        )

    if index < 0:
        raise ValueError(
            "index cannot be negative"
        )

    total = search_space_size(
        alphabet,
        length,
    )

    if index >= total:
        raise IndexError(
            "index is outside the search space"
        )

    base = len(alphabet)

    result = [""] * length

    remaining = index

    for position in range(
        length - 1,
        -1,
        -1,
    ):
        result[position] = alphabet[
            remaining % base
        ]

        remaining //= base

    return "".join(result)


def exhaustive_candidates(
    alphabet: str,
    length: int,
    start: int = 0,
    limit: int | None = None,
) -> Iterator[tuple[int, str]]:
    """
    Generate candidates from a deterministic search space.

    start:
        First position to process.

    limit:
        Maximum number of positions to yield.
    """

    total = search_space_size(
        alphabet,
        length,
    )

    if start < 0:
        raise ValueError(
            "start cannot be negative"
        )

    if start >= total:
        return

    end = total

    if limit is not None:
        if limit < 1:
            return

        end = min(
            start + limit,
            total,
        )

    for index in range(
        start,
        end,
    ):
        yield (
            index,
            candidate_from_index(
                alphabet,
                length,
                index,
            ),
        )
