from pathlib import Path

from forge_engine.jobs.checkpoint import Checkpoint
from forge_engine.jobs.job import Job, JobStatus


class JobManager:

    def __init__(
        self,
        directory: str = ".forge/jobs",
    ):
        self.directory = Path(directory)
        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _checkpoint_path(
        self,
        job_id: str,
    ) -> Path:
        return (
            self.directory
            / f"{job_id}.json"
        )

    def create(
        self,
        mode: str,
    ) -> Job:

        job = Job.create(mode)

        checkpoint = Checkpoint(
            job_id=job.job_id,
            mode=mode,
            position=0,
            generated=0,
            status=JobStatus.CREATED.value,
        )

        checkpoint.save(
            self._checkpoint_path(
                job.job_id
            )
        )

        return job

    def load(
        self,
        job_id: str,
    ) -> Checkpoint:

        path = self._checkpoint_path(
            job_id
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Job not found: {job_id}"
            )

        return Checkpoint.load(path)

    def update(
        self,
        job_id: str,
        position: int,
        generated: int,
        status: str,
    ) -> Checkpoint:

        checkpoint = self.load(job_id)

        checkpoint.position = position
        checkpoint.generated = generated
        checkpoint.status = status

        checkpoint.save(
            self._checkpoint_path(
                job_id
            )
        )

        return checkpoint

    def pause(
        self,
        job_id: str,
        position: int,
        generated: int,
    ) -> Checkpoint:

        return self.update(
            job_id,
            position,
            generated,
            JobStatus.PAUSED.value,
        )

    def complete(
        self,
        job_id: str,
        position: int,
        generated: int,
    ) -> Checkpoint:

        return self.update(
            job_id,
            position,
            generated,
            JobStatus.COMPLETE.value,
        )
