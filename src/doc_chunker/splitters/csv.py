"""Нарезка CSV: заголовок повторяется в каждом чанке."""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence

from doc_chunker.config import ChunkConfig
from doc_chunker.packing import pack_units
from doc_chunker.protocols import TokenCounter
from doc_chunker.splitters.base import FormatSplitter


class CsvSplitter(FormatSplitter):
    """Пакует строки таблицы, оставляя шапку в каждом выходном файле."""

    @property
    def extensions(self) -> tuple[str, ...]:
        return (".csv",)

    def split_content(
        self,
        content: str,
        config: ChunkConfig,
        counter: TokenCounter,
    ) -> list[str]:
        dialect = _detect_dialect(content)
        rows = list(csv.reader(io.StringIO(content), dialect))
        if not rows:
            return [content]

        header, *data_rows = rows
        header_text = _write_rows([header], dialect)
        if not data_rows:
            return [header_text]

        wrapper_tokens = counter.count(header_text)
        units = [_write_rows([row], dialect) for row in data_rows]

        def assemble(parts: Sequence[str]) -> str:
            return header_text + "".join(parts)

        return pack_units(
            units,
            config,
            counter,
            assemble=assemble,
            wrapper_tokens=wrapper_tokens,
            join="",
            split_oversized=_keep_row_unit,
        )


def _detect_dialect(content: str) -> csv.Dialect | type[csv.Dialect]:
    sample = content[:4096]
    try:
        return csv.Sniffer().sniff(sample)
    except csv.Error:
        return csv.excel


def _write_rows(rows: list[list[str]], dialect: csv.Dialect | type[csv.Dialect]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, dialect)
    writer.writerows(rows)
    return buffer.getvalue()


def _keep_row_unit(text: str, max_tokens: int, counter: TokenCounter) -> list[str]:
    """Строку CSV не режем посередине кавычек."""
    del max_tokens, counter
    return [text]
