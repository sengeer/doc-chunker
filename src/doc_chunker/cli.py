"""Точка входа командной строки."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from doc_chunker.config import DEFAULT_ENCODING, DEFAULT_MAX_RATIO, ChunkConfig
from doc_chunker.pipeline import ChunkPipeline
from doc_chunker.tokens import TiktokenTokenCounter

KNOWN_ENCODINGS = ("cl100k_base", "o200k_base", "p50k_base")


def build_parser() -> argparse.ArgumentParser:
    """Собрать парсер аргументов CLI."""
    parser = argparse.ArgumentParser(
        prog="doc-chunker",
        description=(
            "Делит файлы из папки input на семантические чанки "
            "под контекстное окно LLM. --size 16 означает 16K токенов (16384)."
        ),
    )
    parser.add_argument(
        "--size",
        type=int,
        required=True,
        metavar="K",
        help="Размер окна в тысячах токенов: 16 → 16384 токена (16K).",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("input"),
        help="Папка с исходными файлами (по умолчанию ./input).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Папка для чанков (по умолчанию ./output).",
    )
    parser.add_argument(
        "--encoding",
        default=DEFAULT_ENCODING,
        choices=KNOWN_ENCODINGS,
        help=f"Кодировка tiktoken (по умолчанию {DEFAULT_ENCODING}).",
    )
    parser.add_argument(
        "--max-ratio",
        type=float,
        default=DEFAULT_MAX_RATIO,
        help=(
            "Множитель мягкого лимита, чтобы не резать единицу посередине "
            f"(по умолчанию {DEFAULT_MAX_RATIO})."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Запустить нарезку и вернуть код выхода процесса."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = ChunkConfig.from_size_k(
            args.size,
            max_ratio=args.max_ratio,
            encoding=args.encoding,
        )
    except ValueError as error:
        parser.error(str(error))

    counter = TiktokenTokenCounter(args.encoding)
    pipeline = ChunkPipeline(
        config,
        counter,
        on_message=lambda message: print(message, file=sys.stderr),
    )
    try:
        written = pipeline.run(args.input, args.output)
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        return 2

    print(f"Записано файлов: {len(written)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
