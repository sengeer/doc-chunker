"""Реестр splitter-стратегий по расширению файла."""

from __future__ import annotations

from collections.abc import Iterable

from doc_chunker.protocols import Splitter
from doc_chunker.splitters.csv import CsvSplitter
from doc_chunker.splitters.html import HtmlSplitter
from doc_chunker.splitters.json import JsonSplitter
from doc_chunker.splitters.markdown import MarkdownSplitter
from doc_chunker.splitters.text import TextSplitter
from doc_chunker.splitters.toml import TomlSplitter
from doc_chunker.splitters.xml import XmlSplitter
from doc_chunker.splitters.yaml import YamlSplitter


class SplitterRegistry:
    """Сопоставляет расширение файла конкретной стратегии нарезки."""

    def __init__(self, splitters: Iterable[Splitter]) -> None:
        self._by_extension: dict[str, Splitter] = {}
        for splitter in splitters:
            for extension in splitter.extensions:
                self._by_extension[extension.lower()] = splitter

    def get(self, suffix: str) -> Splitter | None:
        """Найти splitter по расширению (с точкой) или вернуть None."""
        return self._by_extension.get(suffix.lower())

    def supported_extensions(self) -> tuple[str, ...]:
        """Отсортированный список известных расширений."""
        return tuple(sorted(self._by_extension))

    @classmethod
    def default(cls) -> SplitterRegistry:
        """Реестр со всеми встроенными форматами."""
        return cls(
            (
                XmlSplitter(),
                JsonSplitter(),
                YamlSplitter(),
                TomlSplitter(),
                CsvSplitter(),
                HtmlSplitter(),
                MarkdownSplitter(),
                TextSplitter(),
            )
        )
