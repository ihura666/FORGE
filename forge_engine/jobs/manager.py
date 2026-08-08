from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from forge_engine.core.config import (
    GenerationConfig,
    GenerationMode,
    TraversalMode,
)
from forge_engine.jobs.job import (
    GenerationJob,
    JobStatus,
)


class JobManager:
    """
    Persistent manager for FORGE generation jobs.

    Responsibilities:
    - create jobs
    - persist jobs
    - load jobs
    - pause/resume jobs
    - execute generation jobs
    - maintain output/checkpoint files
    """

    DEFAULT_REQUIRED_LENGTH = 8
    DEFAULT_MAX_CANDIDATES = 1000
    DEFAULT_TRAVERSAL = TraversalMode.SEQUENTIAL

    def __init__(
        self,
        directory: str | Path | None = None,
    ) -> None:
        self.directory = Path(
            directory
            if directory is not None
            else ".forge/jobs"
        )

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ------------------------------------------------------------------
    # PATH MANAGEMENT
    # ------------------------------------------------------------------

    def _job_path(
        self,
        job_id: str,
    ) -> Path:
        return self.directory / f"{job_id}.json"

    def _default_output_path(
        self,
        job_id: str,
    ) -> Path:
        return self.directory / f"{job_id}.txt"

    def _default_checkpoint_path(
        self,
        job_id: str,
    ) -> Path:
        return self.directory / f"{job_id}.state"

    # ------------------------------------------------------------------
    # JOB CREATION
    # ------------------------------------------------------------------

    def create(
        self,
        mode: str,
    ) -> GenerationJob:

        if not isinstance(mode, str):
            raise TypeError(
                "mode must be a string"
            )

        mode = mode.strip().lower()

        if not mode:
            raise ValueError(
                "mode cannot be empty"
            )

        if mode not in {
            "exhaustive",
            "smart",
            "scrambled",
        }:
            raise ValueError(
                f"unsupported generation mode: {mode}"
            )

        job_id = (
            "F-"
            + uuid.uuid4().hex
        )

        output_path = self._default_output_path(
            job_id
        )

        checkpoint_path = self._default_checkpoint_path(
            job_id
        )

        config = GenerationConfig(
            mode=GenerationMode(mode),
            traversal=self.DEFAULT_TRAVERSAL,
            required_length=self.DEFAULT_REQUIRED_LENGTH,
            max_candidates=self.DEFAULT_MAX_CANDIDATES,
            keywords=[],
            numbers=[],
            symbols=[],
        )

        job = GenerationJob(
            job_id=job_id,
            config=config,
            output_path=output_path,
            checkpoint_path=checkpoint_path,
        )

        self._save(job)

        return job

    # ------------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------------

    def _save(
        self,
        job: GenerationJob,
    ) -> GenerationJob:

        path = self._job_path(
            job.job_id
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = self._job_to_dict(
            job
        )

        temporary = path.with_suffix(
            ".json.tmp"
        )

        temporary.write_text(
            json.dumps(
                data,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        temporary.replace(path)

        return job

    # ------------------------------------------------------------------
    # LOAD
    # ------------------------------------------------------------------

    def load(
        self,
        job_id: str,
    ) -> GenerationJob:

        if not isinstance(job_id, str):
            raise TypeError(
                "job_id must be a string"
            )

        path = self._job_path(
            job_id
        )

        if not path.exists():
            raise FileNotFoundError(
                f"job not found: {job_id}"
            )

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        job = self._job_from_dict(
            data
        )

        return job

    # ------------------------------------------------------------------
    # PAUSE
    # ------------------------------------------------------------------

    def pause(
        self,
        job_id: str,
        position: Optional[int] = None,
        generated: Optional[int] = None,
    ) -> GenerationJob:

        job = self.load(
            job_id
        )

        if position is not None:
            if position < 0:
                raise ValueError(
                    "position cannot be negative"
                )

            self._set_position(
                job,
                position,
            )

        if generated is not None:
            if generated < 0:
                raise ValueError(
                    "generated cannot be negative"
                )

            self._set_generated(
                job,
                generated,
            )

        job.status = JobStatus.PAUSED

        self._touch(job)

        self._save(job)

        self._write_checkpoint(job)

        return job

    # ------------------------------------------------------------------
    # RESUME
    # ------------------------------------------------------------------

    def resume(
        self,
        job_id: str,
    ) -> GenerationJob:

        job = self.load(
            job_id
        )

        job.status = JobStatus.RUNNING

        self._touch(job)

        self._save(job)

        self._write_checkpoint(job)

        return job

    # ------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------

    def status(
        self,
        job_id: str,
    ) -> GenerationJob:

        return self.load(
            job_id
        )

    # ------------------------------------------------------------------
    # RUN
    # ------------------------------------------------------------------

    def run(
        self,
        job: GenerationJob,
    ) -> int:

        if not isinstance(
            job,
            GenerationJob,
        ):
            raise TypeError(
                "job must be a GenerationJob"
            )

        job.status = JobStatus.RUNNING

        self._touch(job)

        self._save(job)

        generator = self._build_generator(
            job
        )

        generated = 0

        output_path = self._ensure_output_path(
            job
        )

        checkpoint_path = self._ensure_checkpoint_path(
            job
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        checkpoint_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        candidates = list(
            generator
        )

        limit = int(
            job.config.max_candidates
        )

        selected = candidates[:limit]

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as handle:

            for index, candidate in enumerate(
                selected
            ):

                handle.write(
                    f"{candidate}\n"
                )

                generated += 1

                self._set_position(
                    job,
                    index + 1,
                )

                self._set_generated(
                    job,
                    generated,
                )

        job.status = JobStatus.COMPLETED

        self._touch(job)

        self._save(job)

        self._write_checkpoint(job)

        return generated

    # ------------------------------------------------------------------
    # GENERATOR
    # ------------------------------------------------------------------

    def _build_generator(
        self,
        job: GenerationJob,
    ):
        """
        Build a generator through the actual FORGE factory.

        The project stores the factory at:
            forge_engine.core.factory
        """

        factory = self._get_factory()

        config = job.config

        if config is None:
            config = self._make_config(
                job
            )

        return self._create_from_factory(
            factory,
            config,
        )

    # ------------------------------------------------------------------
    # FACTORY DISCOVERY
    # ------------------------------------------------------------------

    @staticmethod
    def _get_factory():

        from forge_engine.core import factory

        return factory

    # ------------------------------------------------------------------
    # FACTORY INVOCATION
    # ------------------------------------------------------------------

    @staticmethod
    def _create_from_factory(
        factory: Any,
        config: GenerationConfig,
    ):
        """
        Use the project's existing create_engine() function.
        """

        create_engine = getattr(
            factory,
            "create_engine",
            None,
        )

        if create_engine is None:
            raise ImportError(
                "forge_engine.core.factory does not "
                "provide create_engine()"
            )

        try:
            engine = create_engine(
                config
            )
        except TypeError:
            engine = create_engine(
                config.mode,
                config,
            )

        if engine is None:
            raise RuntimeError(
                "FORGE factory returned None"
            )

        # Prefer the engine's generate method.
        generate = getattr(
            engine,
            "generate",
            None,
        )

        if callable(generate):
            return generate()

        # Some FORGE engines expose candidates
        # through run().
        run = getattr(
            engine,
            "run",
            None,
        )

        if callable(run):
            return run()

        # Some engines are themselves iterable.
        if hasattr(
            engine,
            "__iter__",
        ):
            return engine

        raise TypeError(
            "FORGE engine does not expose "
            "generate(), run(), or iteration"
        )

    # ------------------------------------------------------------------
    # CONFIGURATION
    # ------------------------------------------------------------------

    @staticmethod
    def _make_config(
        job: GenerationJob,
    ) -> GenerationConfig:

        mode = getattr(
            job,
            "mode",
            "exhaustive",
        )

        if isinstance(
            mode,
            GenerationMode,
        ):
            generation_mode = mode
        else:
            generation_mode = GenerationMode(
                str(mode).lower()
            )

        traversal = getattr(
            job,
            "traversal",
            "sequential",
        )

        if isinstance(
            traversal,
            TraversalMode,
        ):
            traversal_mode = traversal
        else:
            traversal_mode = TraversalMode(
                str(traversal).lower()
            )

        return GenerationConfig(
            mode=generation_mode,
            traversal=traversal_mode,
            required_length=int(
                getattr(
                    job,
                    "required_length",
                    JobManager.DEFAULT_REQUIRED_LENGTH,
                )
            ),
            max_candidates=int(
                getattr(
                    job,
                    "max_candidates",
                    JobManager.DEFAULT_MAX_CANDIDATES,
                )
            ),
            keywords=list(
                getattr(
                    job,
                    "keywords",
                    [],
                )
            ),
            numbers=list(
                getattr(
                    job,
                    "numbers",
                    [],
                )
            ),
            symbols=list(
                getattr(
                    job,
                    "symbols",
                    [],
                )
            ),
        )

    # ------------------------------------------------------------------
    # SERIALIZATION
    # ------------------------------------------------------------------

    @staticmethod
    def _job_to_dict(
        job: GenerationJob,
    ) -> dict[str, Any]:

        config = getattr(
            job,
            "config",
            None,
        )

        if config is None:
            config = JobManager._make_config(
                job
            )

        output_path = (
            getattr(
                job,
                "output_path",
                None,
            )
        )

        checkpoint_path = (
            getattr(
                job,
                "checkpoint_path",
                None,
            )
        )

        if output_path is None:
            output_path = (
                JobManager(
                    directory=Path(".")
                )._default_output_path(
                    job.job_id
                )
            )

        if checkpoint_path is None:
            checkpoint_path = (
                JobManager(
                    directory=Path(".")
                )._default_checkpoint_path(
                    job.job_id
                )
            )

        return {
            "job_id": job.job_id,

            "mode": (
                config.mode.value
                if isinstance(
                    config.mode,
                    GenerationMode,
                )
                else str(config.mode)
            ),

            "traversal": (
                config.traversal.value
                if isinstance(
                    config.traversal,
                    TraversalMode,
                )
                else str(config.traversal)
            ),

            "required_length": int(
                config.required_length
            ),

            "max_candidates": int(
                config.max_candidates
            ),

            "keywords": list(
                config.keywords
            ),

            "numbers": list(
                config.numbers
            ),

            "symbols": list(
                config.symbols
            ),

            "output_path": str(
                output_path
            ),

            "checkpoint_path": str(
                checkpoint_path
            ),

            "status": (
                job.status.value
                if isinstance(
                    job.status,
                    JobStatus,
                )
                else str(job.status)
            ),

            "position": int(
                getattr(
                    job,
                    "position",
                    getattr(
                        job,
                        "current_index",
                        0,
                    ),
                )
            ),

            "generated": int(
                getattr(
                    job,
                    "generated",
                    getattr(
                        job,
                        "total_generated",
                        0,
                    ),
                )
            ),

            "created_at": float(
                getattr(
                    job,
                    "created_at",
                    time.time(),
                )
            ),

            "updated_at": float(
                getattr(
                    job,
                    "updated_at",
                    time.time(),
                )
            ),

            "metadata": dict(
                getattr(
                    job,
                    "metadata",
                    {},
                )
            ),
        }

    # ------------------------------------------------------------------
    # DESERIALIZATION
    # ------------------------------------------------------------------

    def _job_from_dict(
        self,
        data: dict[str, Any],
    ) -> GenerationJob:

        if not isinstance(
            data,
            dict,
        ):
            raise TypeError(
                "job data must be a dictionary"
            )

        return self._job_from_config_dict(
            data
        )

    def _job_from_config_dict(
        self,
        data: dict[str, Any],
    ) -> GenerationJob:

        job_id = str(
            data["job_id"]
        )

        mode_value = data.get(
            "mode",
            "exhaustive",
        )

        traversal_value = data.get(
            "traversal",
            "sequential",
        )

        config = GenerationConfig(
            mode=(
                mode_value
                if isinstance(
                    mode_value,
                    GenerationMode,
                )
                else GenerationMode(
                    str(mode_value).lower()
                )
            ),

            traversal=(
                traversal_value
                if isinstance(
                    traversal_value,
                    TraversalMode,
                )
                else TraversalMode(
                    str(traversal_value).lower()
                )
            ),

            required_length=int(
                data.get(
                    "required_length",
                    self.DEFAULT_REQUIRED_LENGTH,
                )
            ),

            max_candidates=int(
                data.get(
                    "max_candidates",
                    self.DEFAULT_MAX_CANDIDATES,
                )
            ),

            keywords=list(
                data.get(
                    "keywords",
                    [],
                )
            ),

            numbers=list(
                data.get(
                    "numbers",
                    [],
                )
            ),

            symbols=list(
                data.get(
                    "symbols",
                    [],
                )
            ),
        )

        # --------------------------------------------------------------
        # THIS IS THE IMPORTANT FIX.
        #
        # Old job files may contain:
        #
        #   "output_path": null
        #   "checkpoint_path": null
        #
        # Never pass None into pathlib.Path().
        # --------------------------------------------------------------

        raw_output = data.get(
            "output_path"
        )

        raw_checkpoint = data.get(
            "checkpoint_path"
        )

        if raw_output:
            output_path = Path(
                raw_output
            )
        else:
            output_path = self._default_output_path(
                job_id
            )

        if raw_checkpoint:
            checkpoint_path = Path(
                raw_checkpoint
            )
        else:
            checkpoint_path = self._default_checkpoint_path(
                job_id
            )

        job = GenerationJob(
            job_id=job_id,
            config=config,
            output_path=output_path,
            checkpoint_path=checkpoint_path,
        )

        status_value = data.get(
            "status",
            JobStatus.CREATED.value,
        )

        try:
            job.status = (
                status_value
                if isinstance(
                    status_value,
                    JobStatus,
                )
                else JobStatus(
                    str(status_value).lower()
                )
            )
        except ValueError:
            job.status = JobStatus.CREATED

        self._set_position(
            job,
            int(
                data.get(
                    "position",
                    data.get(
                        "current_index",
                        0,
                    ),
                )
            ),
        )

        self._set_generated(
            job,
            int(
                data.get(
                    "generated",
                    data.get(
                        "total_generated",
                        0,
                    ),
                )
            ),
        )

        if "created_at" in data:
            job.created_at = float(
                data["created_at"]
            )

        if "updated_at" in data:
            job.updated_at = float(
                data["updated_at"]
            )

        if "metadata" in data:
            job.metadata = dict(
                data["metadata"]
            )

        return job

    # ------------------------------------------------------------------
    # STATE COMPATIBILITY
    # ------------------------------------------------------------------

    @staticmethod
    def _set_position(
        job: GenerationJob,
        value: int,
    ) -> None:

        value = int(value)

        if hasattr(
            type(job),
            "position",
        ):
            try:
                job.position = value
                return
            except Exception:
                pass

        if hasattr(
            job,
            "set_position",
        ):
            job.set_position(
                value
            )
            return

        if hasattr(
            job,
            "current_index",
        ):
            job.current_index = value
            return

        job.position = value

    @staticmethod
    def _set_generated(
        job: GenerationJob,
        value: int,
    ) -> None:

        value = int(value)

        if hasattr(
            type(job),
            "generated",
        ):
            try:
                job.generated = value
                return
            except Exception:
                pass

        if hasattr(
            job,
            "set_generated",
        ):
            job.set_generated(
                value
            )
            return

        if hasattr(
            job,
            "total_generated",
        ):
            job.total_generated = value
            return

        job.generated = value

    # ------------------------------------------------------------------
    # CHECKPOINT
    # ------------------------------------------------------------------

    def _write_checkpoint(
        self,
        job: GenerationJob,
    ) -> None:

        checkpoint_path = (
            self._ensure_checkpoint_path(
                job
            )
        )

        checkpoint_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        position = int(
            getattr(
                job,
                "position",
                getattr(
                    job,
                    "current_index",
                    0,
                ),
            )
        )

        generated = int(
            getattr(
                job,
                "generated",
                getattr(
                    job,
                    "total_generated",
                    0,
                ),
            )
        )

        checkpoint = {
            "job_id": job.job_id,
            "mode": (
                job.config.mode.value
                if isinstance(
                    job.config.mode,
                    GenerationMode,
                )
                else str(
                    job.config.mode
                )
            ),
            "position": position,
            "generated": generated,
            "status": (
                job.status.value
                if isinstance(
                    job.status,
                    JobStatus,
                )
                else str(
                    job.status
                )
            ),
            "updated_at": time.time(),
        }

        checkpoint_path.write_text(
            json.dumps(
                checkpoint,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # PATH NORMALIZATION
    # ------------------------------------------------------------------

    def _ensure_output_path(
        self,
        job: GenerationJob,
    ) -> Path:

        value = getattr(
            job,
            "output_path",
            None,
        )

        if value:
            path = Path(value)
        else:
            path = self._default_output_path(
                job.job_id
            )

            job.output_path = path

        return path

    def _ensure_checkpoint_path(
        self,
        job: GenerationJob,
    ) -> Path:

        value = getattr(
            job,
            "checkpoint_path",
            None,
        )

        if value:
            path = Path(value)
        else:
            path = self._default_checkpoint_path(
                job.job_id
            )

            job.checkpoint_path = path

        return path

    # ------------------------------------------------------------------
    # TIME
    # ------------------------------------------------------------------

    @staticmethod
    def _touch(
        job: GenerationJob,
    ) -> None:

        job.updated_at = time.time()
