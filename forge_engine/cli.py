from __future__ import annotations

import argparse
import sys
from pathlib import Path

from forge_engine.core.config import (
    GenerationConfig,
    GenerationMode,
    TraversalMode,
)
from forge_engine.core.factory import create_engine


VERSION = "1.0.0"


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
        "--mode",
        choices=[mode.value for mode in GenerationMode],
        default=GenerationMode.EXHAUSTIVE.value,
        help="Generation mode.",
    )

    parser.add_argument(
        "--traversal",
        choices=[mode.value for mode in TraversalMode],
        default=TraversalMode.SEQUENTIAL.value,
        help="Traversal strategy.",
    )

    parser.add_argument(
        "--length",
        type=int,
        required=True,
        help="Required candidate length.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        required=True,
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


def build_config(args: argparse.Namespace) -> GenerationConfig:
    if args.length <= 0:
        raise ValueError("length must be greater than zero")

    if args.limit <= 0:
        raise ValueError("limit must be greater than zero")

    return GenerationConfig(
        mode=GenerationMode(args.mode),
        traversal=TraversalMode(args.traversal),
        required_length=args.length,
        max_candidates=args.limit,
        keywords=args.keywords,
        numbers=args.numbers,
        symbols=args.symbols,
    )


def write_candidates(output: Path, candidates) -> int:
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


def run(args: argparse.Namespace) -> int:
    config = build_config(args)

    engine = create_engine(config)

    candidates = engine.generate()

    generated = write_candidates(
        args.output,
        candidates,
    )

    print(
        f"FORGE completed: {generated} candidates"
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

    except (ValueError, TypeError) as exc:
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
    raise SystemExit(main())
