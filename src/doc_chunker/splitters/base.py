"""Базовый splitter: общие расширения и проверка пустого ввода."""

from __future__ import annotations

from doc_chunker.config import ChunkConfig
from doc_chunker.protocols import Splitter, TokenCounter


class FormatSplitter(Splitter):
    """Общая заготовка для форматных стратегий."""

    def split(
        self,
        content: str,
        config: ChunkConfig,
        counter: TokenCounter,
    ) -> list[str]:
        if content == "":
            return [""]
        return self.split_content(content, config, counter)

    def split_content(
        self,
        content: str,
        config: ChunkConfig,
        counter: TokenCounter,
    ) -> list[str]:
        """Разбить непустой текст; реализуется в конкретных форматах."""
        raise NotImplementedError
