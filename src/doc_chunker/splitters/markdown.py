"""Нарезка Markdown по заголовкам и абзацам."""

from __future__ import annotations

import re
from collections.abc import Sequence

from doc_chunker.config import ChunkConfig
from doc_chunker.packing import pack_units
from doc_chunker.protocols import TokenCounter
from doc_chunker.splitters.base import FormatSplitter

_HEADING_SPLIT = re.compile(r"(?m)(?=^#{1,6}\s)")
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")


class MarkdownSplitter(FormatSplitter):
    """Сначала секции ``#``…``######``, при переполнении — абзацы."""

    @property
    def extensions(self) -> tuple[str, ...]:
        return (".md",)

    def split_content(
        self,
        content: str,
        config: ChunkConfig,
        counter: TokenCounter,
    ) -> list[str]:
        units = _markdown_units(content)
        if counter.count(content) <= config.target_tokens:
            return [content]

        def assemble(parts: Sequence[str]) -> str:
            return "".join(parts)

        return pack_units(
            units,
            config,
            counter,
            assemble=assemble,
            wrapper_tokens=0,
            join="",
            starts_new_chunk=lambda unit: unit.lstrip().startswith("#"),
        )


def _markdown_units(content: str) -> list[str]:
    heading_parts = [part for part in _HEADING_SPLIT.split(content) if part]
    if len(heading_parts) > 1:
        return heading_parts
    paragraphs = _PARAGRAPH_SPLIT.split(content)
    if len(paragraphs) <= 1:
        return [content] if content else [""]
    units: list[str] = []
    for index, paragraph in enumerate(paragraphs):
        if index < len(paragraphs) - 1:
            units.append(paragraph + "\n\n")
        else:
            units.append(paragraph)
    return units
