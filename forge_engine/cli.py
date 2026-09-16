from __future__ import annotations

import argparse
import sys
from pathlib import Path

from forge_engine.core.checkpoint import (
    Checkpoint,
    checkpoint_path,
    load_checkpoint,
    save_checkpoint,
)
from forge_engine.core.config import (
    GenerationConfig,
    GenerationMode,
    TraversalMode,
)
from forge_engine.core.factory import create_engine


VERSION = "1.0.4"

FREE_LIMIT = 1_000_000


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="FORGE",
        description=(
            "FORGE generation engine: "
            "password and email dictionary generation."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"FORGE {VERSION}",
    )

    parser.add_argument(
        "--free",
        action="store_true",
        help=(
            "Run FORGE in free mode. "
            "Maximum output is 1,000,000 candidates."
        ),
    )

    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in GenerationMode],
        default=None,
        help="Generation mode.",
    )

    parser.add_argument(
        "--traversal",
        choices=[mode.value for mode in TraversalMode],
        default=None,
        help="Traversal strategy.",
    )

    length_group = parser.add_mutually_exclusive_group(required=True)

    length_group.add_argument(
        "--length",
        type=int,
        help="Required candidate length.",
    )

    length_group.add_argument(
        "--min-length",
        type=int,
        help="Minimum candidate length for range generation.",
    )

    length_group.add_argument(
        "--resume",
        action="store_true",
        help="Resume a previous generation from the output file.",
    )

    parser.add_argument(
        "--max-length",
        type=int,
        help="Maximum candidate length for range generation.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        required=False,
        default=None,
        help="Maximum number of candidates.",
    )

    parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        dest="keywords",
        help="Keyword input. May be supplied multiple times.",
    )

    parser.add_argument(
        "--number",
        action="append",
        default=[],
        dest="numbers",
        help="Numeric input. May be supplied multiple times.",
    )

    parser.add_argument(
        "--symbol",
        action="append",
        default=[],
        dest="symbols",
        help="Symbol input. May be supplied multiple times.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output.txt"),
        help="Output file.",
    )

    return parser


def build_config(
    args: argparse.Namespace,
    length: int | None = None,
    limit: int | None = None,
) -> GenerationConfig:

    if length is None:
        length = args.length

    if length is None:
        raise ValueError(
            "A length or length range is required"
        )

    if length <= 0:
        raise ValueError(
            "length must be greater than zero"
        )

    if limit is None:
        limit = args.limit

    if limit <= 0:
        raise ValueError(
            "limit must be greater than zero"
        )

    if not args.keywords:
        raise ValueError(
            "At least one keyword is required"
        )

    if args.free:
        effective_limit = min(
            limit,
            FREE_LIMIT,
        )
    else:
        effective_limit = limit

    return GenerationConfig(
        mode=GenerationMode(args.mode),
        traversal=TraversalMode(args.traversal),
        required_length=length,
        max_candidates=effective_limit,
        keywords=args.keywords,
        numbers=args.numbers,
        symbols=args.symbols,
    )


def write_candidates(
    output: Path,
    candidates,
) -> int:

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    count = 0

    with output.open(
        "w",
        encoding="utf-8",
    ) as handle:

        for candidate in candidates:

            value = getattr(
                candidate,
                "value",
                str(candidate),
            )

            handle.write(
                f"{value}\n"
            )

            count += 1

    return count


def run(
    args: argparse.Namespace,
) -> int:

    if args.resume:
        return resume_generation(args)

    if args.mode is None:
        args.mode = GenerationMode.SMART

    if args.traversal is None:
        args.traversal = TraversalMode.SEQUENTIAL

    if args.limit <= 0:
        raise ValueError(
            "limit must be greater than zero"
        )

    if args.min_length is not None:

        if args.max_length is None:
            raise ValueError(
                "--max-length is required with --min-length"
            )

        if args.min_length <= 0:
            raise ValueError(
                "min-length must be greater than zero"
            )

        if args.max_length <= 0:
            raise ValueError(
                "max-length must be greater than zero"
            )

        if args.min_length > args.max_length:
            raise ValueError(
                "min-length cannot be greater than max-length"
            )

        lengths = list(
            range(
                args.min_length,
                args.max_length + 1,
            )
        )

    else:

        if args.max_length is not None:
            raise ValueError(
                "--max-length requires --min-length"
            )

        if args.length is None:
            raise ValueError(
                "A length or length range is required"
            )

        if args.length <= 0:
            raise ValueError(
                "length must be greater than zero"
            )

        lengths = [args.length]

    if not args.keywords:
        raise ValueError(
            "At least one keyword is required"
        )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if args.free:
        effective_limit = min(
            args.limit,
            FREE_LIMIT,
        )
    else:
        effective_limit = args.limit

    state_path = checkpoint_path(args.output)

    checkpoint = Checkpoint(
        version=1,
        output=str(args.output.resolve()),
        mode=args.mode,
        traversal=args.traversal,
        lengths=lengths,
        current_length_index=0,
        current_position=0,
        generated=0,
        limit=effective_limit,
        keywords=list(args.keywords),
        numbers=list(args.numbers),
        symbols=list(args.symbols),
        completed=False,
    )

    save_checkpoint(
        state_path,
        checkpoint,
    )

    generated = 0
    remaining = effective_limit

    with args.output.open(
        "w",
        encoding="utf-8",
    ) as handle:

        for length_index, length in enumerate(lengths):

            if remaining <= 0:
                break

            checkpoint.current_length_index = length_index
            checkpoint.current_position = 0

            save_checkpoint(
                state_path,
                checkpoint,
            )

            config = build_config(
                args,
                length=length,
                limit=remaining,
            )

            engine = create_engine(config)

            for candidate in engine.generate(
                start=checkpoint.current_position,
            ):

                value = getattr(
                    candidate,
                    "value",
                    str(candidate),
                )

                handle.write(
                    f"{value}\n"
                )
                handle.flush()

                generated += 1
                remaining -= 1

                checkpoint.generated = generated
                checkpoint.current_position += 1

                save_checkpoint(
                    state_path,
                    checkpoint,
                )

                if remaining <= 0:
                    break

        checkpoint.current_length_index = len(lengths)
        checkpoint.current_position = 0

        checkpoint.completed = (
            generated >= effective_limit
            or checkpoint.current_length_index >= len(lengths)
        )
        save_checkpoint(
            state_path,
            checkpoint,
        )

    print(
        f"FORGE completed: {generated} candidates"
    )

    print(
        f"Output: {args.output}"
    )

    if args.free:

        if args.limit > FREE_LIMIT:

            print(
                "Free mode limit applied: "
                f"{FREE_LIMIT:,} candidates"
            )

        else:

            print(
                "FORGE Free Mode: "
                f"maximum {FREE_LIMIT:,} candidates"
            )

    return 0


def resume_generation(
    args: argparse.Namespace,
) -> int:

    if args.length is not None:
        raise ValueError(
            "--resume cannot be combined with --length"
        )

    if args.min_length is not None:
        raise ValueError(
            "--resume cannot be combined with --min-length"
        )

    if args.max_length is not None:
        raise ValueError(
            "--resume cannot be combined with --max-length"
        )

    if args.limit is not None:
        raise ValueError(
            "--resume cannot be combined with --limit"
        )

    if args.keywords:
        raise ValueError(
            "--resume cannot be combined with --keyword"
        )

    if args.numbers:
        raise ValueError(
            "--resume cannot be combined with --number"
        )

    if args.symbols:
        raise ValueError(
            "--resume cannot be combined with --symbol"
        )

    if args.mode is not None:
        raise ValueError(
            "--resume cannot be combined with --mode"
        )

    if args.traversal is not None:
        raise ValueError(
            "--resume cannot be combined with --traversal"
        )

    state_path = checkpoint_path(args.output)
    checkpoint = load_checkpoint(state_path)

    resolved_output = str(
        args.output.resolve()
    )

    if checkpoint.output != resolved_output:
        raise ValueError(
            "Resume state does not belong to this output file"
        )

    if checkpoint.completed:
        print(
            f"FORGE task already completed: "
            f"{args.output}"
        )
        return 0

    remaining = (
        checkpoint.limit
        - checkpoint.generated
    )

    if remaining <= 0:
        checkpoint.completed = True
        save_checkpoint(
            state_path,
            checkpoint,
        )
        print(
            f"FORGE task already reached its limit: "
            f"{args.output}"
        )
        return 0

    class ResumeArgs:
        pass

    resume_args = ResumeArgs()
    resume_args.mode = GenerationMode(
        checkpoint.mode
    )
    resume_args.traversal = TraversalMode(
        checkpoint.traversal
    )
    resume_args.limit = remaining
    resume_args.free = False
    resume_args.keywords = checkpoint.keywords
    resume_args.numbers = checkpoint.numbers
    resume_args.symbols = checkpoint.symbols

    generated_now = 0

    with args.output.open(
        "a",
        encoding="utf-8",
    ) as handle:

        for index in range(
            checkpoint.current_length_index,
            len(checkpoint.lengths),
        ):

            if remaining <= 0:
                break

            length = checkpoint.lengths[index]

            resume_args.length = length

            config = build_config(
                resume_args,
                length=length,
                limit=remaining,
            )

            engine = create_engine(config)

            for candidate in engine.generate(
                start=checkpoint.current_position,
            ):

                value = getattr(
                    candidate,
                    "value",
                    str(candidate),
                )

                handle.write(
                    f"{value}\n"
                )
                handle.flush()

                generated_now += 1
                checkpoint.generated += 1
                checkpoint.current_position += 1
                remaining -= 1

                save_checkpoint(
                    state_path,
                    checkpoint,
                )

                if remaining <= 0:
                    break

            checkpoint.current_length_index = index + 1
            checkpoint.current_position = 0

            save_checkpoint(
                state_path,
                checkpoint,
            )

    checkpoint.completed = (
        checkpoint.generated >= checkpoint.limit
        or checkpoint.current_length_index
        >= len(checkpoint.lengths)
    )

    if checkpoint.completed:
        checkpoint.current_position = 0

    save_checkpoint(
        state_path,
        checkpoint,
    )

    print(
        f"FORGE resumed: {generated_now} candidates"
    )

    print(
        f"Total candidates: {checkpoint.generated}"
    )

    print(
        f"Output: {args.output}"
    )

    return 0

def main(argv=None) -> int:

    parser = build_parser()

    try:

        args = parser.parse_args(argv)

        return run(args)

    except KeyboardInterrupt:

        print(
            "\nFORGE interrupted.",
            file=sys.stderr,
        )

        return 130

    except (
        ValueError,
        TypeError,
    ) as exc:

        print(
            f"FORGE error: {exc}",
            file=sys.stderr,
        )

        return 2

    except Exception as exc:

        print(
            f"FORGE fatal error: {exc}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
