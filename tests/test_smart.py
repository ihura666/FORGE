from forge_engine.core.config import (
    GenerationConfig,
    GenerationMode,
    TraversalMode,
)

from forge_engine.modes.smart import (
    SmartEngine,
)


def make_config(
    keywords,
    length,
    numbers=None,
    symbols=None,
):

    return GenerationConfig(
        mode=GenerationMode.SMART,
        traversal=TraversalMode.SEQUENTIAL,
        required_length=length,
        max_candidates=100,
        keywords=keywords,
        numbers=numbers or [],
        symbols=symbols or [],
    )


def test_smart_exact_keyword():

    config = make_config(
        ["hello"],
        5,
    )

    engine = SmartEngine(config)

    results = list(
        engine.generate()
    )

    values = [
        item.value
        for item in results
    ]

    assert "hello" in values


def test_smart_numeric_extension():

    config = make_config(
        ["abcd"],
        5,
        numbers=["1"],
    )

    engine = SmartEngine(config)

    results = list(
        engine.generate()
    )

    values = [
        item.value
        for item in results
    ]

    assert "abcd1" in values
    assert "1abcd" in values


def test_smart_symbol_extension():

    config = make_config(
        ["abcd"],
        5,
        symbols=["@"],
    )

    engine = SmartEngine(config)

    results = list(
        engine.generate()
    )

    values = [
        item.value
        for item in results
    ]

    assert "abcd@" in values
    assert "@abcd" in values


def test_smart_respects_length():

    config = make_config(
        ["hello"],
        4,
    )

    engine = SmartEngine(config)

    results = list(
        engine.generate()
    )

    for candidate in results:
        assert len(candidate.value) == 4
