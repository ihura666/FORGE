from forge_engine.jobs.manager import JobManager
from forge_engine.modes.exhaustive import (
    exhaustive_candidates,
)


class ExhaustiveRunner:

    def __init__(
        self,
        job_manager: JobManager,
    ):
        self.jobs = job_manager

    def run(
        self,
        job_id: str,
        alphabet: str,
        length: int,
        limit: int,
    ):

        checkpoint = self.jobs.load(
            job_id
        )

        start = checkpoint.position

        generated = checkpoint.generated

        for position, candidate in (
            exhaustive_candidates(
                alphabet=alphabet,
                length=length,
                start=start,
                limit=limit,
            )
        ):

            generated += 1

            yield candidate

            self.jobs.update(
                job_id=job_id,
                position=position + 1,
                generated=generated,
                status="running",
            )

        self.jobs.complete(
            job_id=job_id,
            position=start + limit,
            generated=generated,
        )
