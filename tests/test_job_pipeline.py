from forge_engine.core.config import (
    GenerationConfig,
    GenerationMode,
    TraversalMode,
)
from forge_engine.jobs.job import GenerationJob
from forge_engine.jobs.manager import JobManager


def test_job_pipeline(tmp_path):

    output = tmp_path / "output.txt"
    checkpoint = tmp_path / "output.state"

    config = GenerationConfig(
        mode=GenerationMode.EXHAUSTIVE,
        traversal=TraversalMode.SEQUENTIAL,
        required_length=2,
        max_candidates=5,
        keywords=["abc"],
        numbers=[],
        symbols=[],
    )

    job = GenerationJob(
        job_id="test-001",
        config=config,
        output_path=output,
        checkpoint_path=checkpoint,
    )

    manager = JobManager()

    generated = manager.run(job)

    assert generated == 5
    assert output.exists()
    assert checkpoint.exists()

    lines = output.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 5

    values = [
        line.split("value='", 1)[1].split("'", 1)[0]
        for line in lines
    ]

    assert all(len(value) == 2 for value in values)
    assert len(set(values)) == 5
