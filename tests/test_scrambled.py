from forge_engine.core.config import (
    GenerationConfig,
    GenerationMode,
    TraversalMode,
)

from forge_engine.modes.scrambled import (
    ScrambledEngine,
)


def test_scrambled_exact_length():

    config = GenerationConfig(
        mode=GenerationMode.SCRAMBLED,
        traversal=TraversalMode.SEQUENTIAL,
        required_length=3,
        max_candidates=100,
        keywords=["abcd"],
        numbers=[],
        symbols=[],
    )

    engine = ScrambledEngine(
        config
    )

    results = list(
        engine.generate()
    )

    assert results

    for candidate in results:
        assert len(candidate.value) == 3


def test_scrambled_no_duplicates():

    config = GenerationConfig(
        mode=GenerationMode.SCRAMBLED,
        traversal=TraversalMode.SEQUENTIAL,
        required_length=2,
        max_candidates=100,
        keywords=["aabc"],
        numbers=[],
        symbols=[],
    )

    engine = ScrambledEngine(
        config
    )

    values = [
        item.value
        for item in engine.generate()
    ]

    assert len(values) == len(set(values))


def test_scrambled_limit():

    config = GenerationConfig(
        mode=GenerationMode.SCRAMBLED,
        traversal=TraversalMode.SEQUENTIAL,
        required_length=3,
        max_candidates=5,
        keywords=["abcdef"],
        numbers=[],
        symbols=[],
    )

    engine = ScrambledEngine(
        config
    )

    results = list(
        engine.generate()
    )

    assert len(results) == 5
