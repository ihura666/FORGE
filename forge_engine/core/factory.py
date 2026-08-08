from forge_engine.core.config import (
    GenerationConfig,
    GenerationMode,
)

from forge_engine.core.engine import (
    GenerationEngine,
)

from forge_engine.modes.exhaustive import (
    ExhaustiveEngine,
)

from forge_engine.modes.scrambled import (
    ScrambledEngine,
)

from forge_engine.modes.smart import (
    SmartEngine,
)


def create_engine(
    config: GenerationConfig,
) -> GenerationEngine:

    if config.mode == GenerationMode.SMART:
        return SmartEngine(config)

    if config.mode == GenerationMode.SCRAMBLED:
        return ScrambledEngine(config)

    if config.mode == GenerationMode.EXHAUSTIVE:
        return ExhaustiveEngine(config)

    raise ValueError(
        f"Unsupported generation mode: "
        f"{config.mode}"
    )
