from pathlib import Path

from forge_engine.cli import main


def test_cli_generates_output(tmp_path):
    output = tmp_path / "output.txt"

    result = main(
        [
            "--mode",
            "exhaustive",
            "--traversal",
            "sequential",
            "--length",
            "2",
            "--limit",
            "4",
            "--keyword",
            "ab",
            "--output",
            str(output),
        ]
    )

    assert result == 0
    assert output.exists()

    lines = output.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 4
    assert all(len(line) == 2 for line in lines)


def test_cli_rejects_invalid_length(tmp_path):
    output = tmp_path / "output.txt"

    result = main(
        [
            "--mode",
            "exhaustive",
            "--length",
            "0",
            "--limit",
            "5",
            "--output",
            str(output),
        ]
    )

    assert result == 2
    assert not output.exists()


def test_cli_rejects_invalid_limit(tmp_path):
    output = tmp_path / "output.txt"

    result = main(
        [
            "--mode",
            "exhaustive",
            "--length",
            "2",
            "--limit",
            "0",
            "--output",
            str(output),
        ]
    )

    assert result == 2
    assert not output.exists()


def test_cli_supports_numbers_and_symbols(tmp_path):
    output = tmp_path / "output.txt"

    result = main(
        [
            "--mode",
            "exhaustive",
            "--length",
            "2",
            "--limit",
            "5",
            "--keyword",
            "ab",
            "--number",
            "12",
            "--symbol",
            "@",
            "--output",
            str(output),
        ]
    )

    assert result == 0
    assert output.exists()

    lines = output.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) <= 5
    assert all(len(line) == 2 for line in lines)
