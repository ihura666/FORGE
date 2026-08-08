from pathlib import Path

from forge_engine.core.engine import (
    GenerationEngine,
)

from forge_engine.jobs.checkpoint import (
    CheckpointManager,
)


class JobExecutor:

    def __init__(
        self,
        engine: GenerationEngine,
        output_path: Path,
        checkpoint: CheckpointManager,
    ):
        self.engine = engine
        self.output_path = output_path
        self.checkpoint = checkpoint

    def run(self) -> int:

        state = (
            self.checkpoint.load()
        )

        start = state.get(
            "position",
            0,
        )

        generated = 0

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.output_path.open(
            "a",
            encoding="utf-8",
        ) as output:

            for candidate in self.engine.generate(
                start=start,
            ):

                output.write(
                    candidate.value
                    + "\n"
                )

                generated += 1

                self.checkpoint.save(
                    {
                        "position":
                            candidate.index + 1,
                        "generated":
                            generated,
                    }
                )

        return generated
