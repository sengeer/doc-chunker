"""Нарезка обычного текста и логов по абзацам и строкам."""

from __future__ import annotations

from collections.abc import Sequence

from doc_chunker.config import ChunkConfig
from doc_chunker.packing import pack_units
from doc_chunker.protocols import TokenCounter
from doc_chunker.splitters.base import FormatSplitter


class TextSplitter(FormatSplitter):
    """Делит ``.txt``/``.log`` по пустым строкам, затем по строкам."""

    @property
    def extensions(self) -> tuple[str, ...]:
        return (".txt", ".log")

    def split_content(
        self,
        content: str,
        config: ChunkConfig,
        counter: TokenCounter,
    ) -> list[str]:
        if counter.count(content) <= config.target_tokens:
            return [content]

        units = _text_units(content)

        def assemble(parts: Sequence[str]) -> str:
            return "".join(parts)

        return pack_units(
            units,
            config,
            counter,
            assemble=assemble,
            wrapper_tokens=0,
            join="",
        )


def _text_units(content: str) -> list[str]:
    if "\n\n" in content:
        parts = content.split("\n\n")
        units = [part + "\n\n" for part in parts[:-1]]
        units.append(parts[-1])
        return [unit for unit in units if unit]
    if "\n" in content:
        parts = content.split("\n")
        units = [part + "\n" for part in parts[:-1]]
        if parts[-1]:
            units.append(parts[-1])
        return [unit for unit in units if unit]
    return [content] if content else [""]
