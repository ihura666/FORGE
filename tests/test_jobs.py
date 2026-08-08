from forge_engine.jobs.job import JobStatus
from forge_engine.jobs.manager import JobManager


def test_job_creation(tmp_path):

    manager = JobManager(
        directory=str(tmp_path)
    )

    job = manager.create(
        "exhaustive"
    )

    assert job.job_id.startswith(
        "F-"
    )

    checkpoint = manager.load(
        job.job_id
    )

    assert checkpoint.mode == "exhaustive"
    assert checkpoint.position == 0
    assert checkpoint.generated == 0
    assert checkpoint.status == (
        JobStatus.CREATED.value
    )


def test_job_pause_and_resume(tmp_path):

    manager = JobManager(
        directory=str(tmp_path)
    )

    job = manager.create(
        "exhaustive"
    )

    manager.pause(
        job.job_id,
        position=500,
        generated=500,
    )

    checkpoint = manager.load(
        job.job_id
    )

    assert checkpoint.position == 500
    assert checkpoint.generated == 500
    assert checkpoint.status == (
        JobStatus.PAUSED.value
    )
