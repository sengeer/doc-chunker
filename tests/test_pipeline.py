"""Интеграционные тесты pipeline и CLI."""

from __future__ import annotations

import json
from pathlib import Path

from doc_chunker.cli import main
from doc_chunker.config import ChunkConfig
from doc_chunker.pipeline import ChunkPipeline
from doc_chunker.tokens import CharTokenCounter, TiktokenTokenCounter


def test_pipeline_writes_numbered_files(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    payload = {"a": "x" * 30, "b": "y" * 30, "c": "z" * 30}
    (input_dir / "document.json").write_text(json.dumps(payload), encoding="utf-8")
    (input_dir / "ignore.bin").write_text("nope", encoding="utf-8")

    messages: list[str] = []
    pipeline = ChunkPipeline(
        ChunkConfig(target_tokens=40),
        CharTokenCounter(),
        on_message=messages.append,
    )
    written = pipeline.run(input_dir, output_dir)
    names = sorted(path.name for path in written)
    assert names[0].startswith("document_")
    assert names[0].endswith(".json")
    assert len(written) >= 2
    assert all(path.parent == output_dir for path in written)
    assert any("Пропуск ignore.bin" in message for message in messages)
    assert any("document.json" in message for message in messages)


def test_cli_size_16_means_16384_tokens(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "note.txt").write_text("короткий текст", encoding="utf-8")

    code = main(
        [
            "--size",
            "16",
            "--input",
            str(input_dir),
            "--output",
            str(output_dir),
        ]
    )
    assert code == 0
    chunk = (output_dir / "note_1.txt").read_text(encoding="utf-8")
    assert chunk == "короткий текст"
    counter = TiktokenTokenCounter()
    assert counter.count(chunk) < 16384
