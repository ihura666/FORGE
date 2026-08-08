from forge_engine.core.config import (
    GenerationConfig,
    GenerationMode,
    TraversalMode,
)

from forge_engine.modes.exhaustive import (
    ExhaustiveEngine,
)


def test_exhaustive_generates_exact_length():

    config = GenerationConfig(
        mode=GenerationMode.EXHAUSTIVE,
        traversal=TraversalMode.SEQUENTIAL,
        required_length=2,
        max_candidates=10,
        keywords=["ab"],
        numbers=[],
        symbols=[],
    )

    engine = ExhaustiveEngine(config)

    results = list(
        engine.generate()
    )

    assert results

    for candidate in results:
        assert len(candidate.value) == 2


def test_exhaustive_uses_numbers():

    config = GenerationConfig(
        mode=GenerationMode.EXHAUSTIVE,
        traversal=TraversalMode.SEQUENTIAL,
        required_length=2,
        max_candidates=20,
        keywords=["ab"],
        numbers=["1"],
        symbols=[],
    )

    engine = ExhaustiveEngine(config)

    values = {
        candidate.value
        for candidate in engine.generate()
    }

    assert "11" in values
    assert "aa" in values
    assert "ab" in values


def test_exhaustive_limit():

    config = GenerationConfig(
        mode=GenerationMode.EXHAUSTIVE,
        traversal=TraversalMode.SEQUENTIAL,
        required_length=4,
        max_candidates=7,
        keywords=["ab"],
        numbers=[],
        symbols=[],
    )

    engine = ExhaustiveEngine(config)

    results = list(
        engine.generate()
    )

    assert len(results) == 7

