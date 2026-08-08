from forge_engine.modes.exhaustive import (
    exhaustive_candidates,
)


def test_exhaustive_length():
    results = list(
        exhaustive_candidates(
            "ab",
            2,
        )
    )

    values = [
        value
        for _, value in results
    ]

    assert values == [
        "aa",
        "ab",
        "ba",
        "bb",
    ]


def test_exhaustive_resume():
    results = list(
        exhaustive_candidates(
            "ab",
            2,
            start=2,
        )
    )

    values = [
        value
        for _, value in results
    ]

    assert values == [
        "ba",
        "bb",
    ]
