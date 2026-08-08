from forge_engine.core.config import (
    GenerationConfig,
    GenerationMode,
    TraversalMode,
)

from forge_engine.core.factory import (
    create_engine,
)


def test_factory_creates_smart():

    config = GenerationConfig(
        mode=GenerationMode.SMART,
        traversal=TraversalMode.SEQUENTIAL,
        required_length=5,
        max_candidates=10,
        keywords=["hello"],
        numbers=[],
        symbols=[],
    )

    engine = create_engine(config)

    assert engine.__class__.__name__ == (
        "SmartEngine"
    )


def test_factory_creates_scrambled():

    config = GenerationConfig(
        mode=GenerationMode.SCRAMBLED,
        traversal=TraversalMode.SEQUENTIAL,
        required_length=3,
        max_candidates=10,
        keywords=["hello"],
        numbers=[],
        symbols=[],
    )

    engine = create_engine(config)

    assert engine.__class__.__name__ == (
        "ScrambledEngine"
    )
