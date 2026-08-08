from forge_engine.modes.exhaustive import (
    candidate_from_index,
    exhaustive_candidates,
    search_space_size,
)


def test_search_space_size():
    assert search_space_size(
        "ab",
        2,
    ) == 4


def test_candidate_from_index():
    assert candidate_from_index(
        "ab",
        2,
        0,
    ) == "aa"

    assert candidate_from_index(
        "ab",
        2,
        1,
    ) == "ab"

    assert candidate_from_index(
        "ab",
        2,
        2,
    ) == "ba"

    assert candidate_from_index(
        "ab",
        2,
        3,
    ) == "bb"


def test_exhaustive_generation():
    results = list(
        exhaustive_candidates(
            "ab",
            2,
        )
    )

    assert results == [
        (0, "aa"),
        (1, "ab"),
        (2, "ba"),
        (3, "bb"),
    ]


def test_exhaustive_resume():
    results = list(
        exhaustive_candidates(
            "ab",
            2,
            start=2,
        )
    )

    assert results == [
        (2, "ba"),
        (3, "bb"),
    ]


def test_exhaustive_limit():
    results = list(
        exhaustive_candidates(
            "ab",
            2,
            start=1,
            limit=2,
        )
    )

    assert results == [
        (1, "ab"),
        (2, "ba"),
    ]
