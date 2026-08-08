from dataclasses import asdict
from pathlib import Path
import json

from .job import GenerationJob, JobStatus


class CheckpointManager:

    def __init__(
        self,
        directory: str | Path = ".forge/checkpoints",
    ):
        self.directory = Path(directory)

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def path_for(
        self,
        job_id: str,
    ) -> Path:

        return (
            self.directory
            / f"{job_id}.json"
        )

    def save(
        self,
        job: GenerationJob,
    ) -> Path:

        path = self.path_for(
            job.job_id
        )

        data = asdict(job)

        data["status"] = job.status.value

        path.write_text(
            json.dumps(
                data,
                indent=4,
            ),
            encoding="utf-8",
        )

        return path

    def load(
        self,
        job_id: str,
    ) -> GenerationJob:

        path = self.path_for(
            job_id
        )

        if not path.exists():

            raise FileNotFoundError(
                f"No checkpoint found for job: {job_id}"
            )

        data = json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )

        data["status"] = JobStatus(
            data["status"]
        )

        return GenerationJob(
            **data
        )

    def exists(
        self,
        job_id: str,
    ) -> bool:

        return self.path_for(
            job_id
        ).exists()

    def delete(
        self,
        job_id: str,
    ) -> None:

        path = self.path_for(
            job_id
        )

        if path.exists():
            path.unlink()

    def list_jobs(self) -> list[str]:

        return sorted(
            path.stem
            for path in self.directory.glob(
                "*.json"
            )
        )
