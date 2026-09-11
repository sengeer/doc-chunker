"""Нарезка HTML по блочным элементам."""

from __future__ import annotations

import re
from collections.abc import Sequence

from doc_chunker.config import ChunkConfig
from doc_chunker.packing import pack_units
from doc_chunker.protocols import TokenCounter
from doc_chunker.splitters.base import FormatSplitter

_BODY_OPEN = re.compile(r"(?is)<body[^>]*>")
_BODY_CLOSE = re.compile(r"(?is)</body>")
_BLOCK_CLOSE = re.compile(
    r"(?i)</(?:p|div|section|article|h[1-6]|li|tr|table|ul|ol|"
    r"blockquote|pre|header|footer|nav|main|aside|figure)>"
)
_DEFAULT_PREFIX = "<html><body>"
_DEFAULT_SUFFIX = "</body></html>"


class HtmlSplitter(FormatSplitter):
    """Режет содержимое ``body`` по закрывающим блочным тегам."""

    @property
    def extensions(self) -> tuple[str, ...]:
        return (".html", ".htm")

    def split_content(
        self,
        content: str,
        config: ChunkConfig,
        counter: TokenCounter,
    ) -> list[str]:
        prefix, inner, suffix = _html_wrapper(content)
        units = _block_units(inner)
        if not units:
            units = [inner] if inner.strip() else [content]
            prefix, suffix = "", ""

        wrapper_tokens = counter.count(prefix + suffix)
        if counter.count(prefix + "".join(units) + suffix) <= config.target_tokens:
            return [prefix + "".join(units) + suffix]

        def assemble(parts: Sequence[str]) -> str:
            return prefix + "".join(parts) + suffix

        return pack_units(
            units,
            config,
            counter,
            assemble=assemble,
            wrapper_tokens=wrapper_tokens,
            join="",
            split_oversized=_keep_markup_unit,
        )


def _html_wrapper(content: str) -> tuple[str, str, str]:
    open_match = _BODY_OPEN.search(content)
    close_match = _BODY_CLOSE.search(content)
    if open_match and close_match and close_match.start() >= open_match.end():
        prefix = content[: open_match.end()]
        inner = content[open_match.end() : close_match.start()]
        suffix = content[close_match.start() :]
        return prefix, inner, suffix
    return _DEFAULT_PREFIX, content, _DEFAULT_SUFFIX


def _block_units(inner: str) -> list[str]:
    units: list[str] = []
    start = 0
    for match in _BLOCK_CLOSE.finditer(inner):
        piece = inner[start : match.end()]
        if piece.strip():
            units.append(piece)
        start = match.end()
    tail = inner[start:]
    if tail.strip():
        units.append(tail)
    return units


def _keep_markup_unit(text: str, max_tokens: int, counter: TokenCounter) -> list[str]:
    """Сохранить блочный HTML целиком, даже если он чуть больше лимита."""
    del max_tokens, counter
    return [text]
