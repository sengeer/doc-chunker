"""Контракты зависимостей pipeline (DIP)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from doc_chunker.config import ChunkConfig


@runtime_checkable
class TokenCounter(Protocol):
    """Счётчик токенов готового текста чанка."""

    def count(self, text: str) -> int:
        """Вернуть число токенов в ``text``."""
        ...

    def encode(self, text: str) -> Sequence[int]:
        """Закодировать текст в идентификаторы токенов."""
        ...

    def decode(self, tokens: Sequence[int]) -> str:
        """Декодировать идентификаторы обратно в текст."""
        ...


class Splitter(ABC):
    """Стратегия нарезки одного семейства форматов."""

    @property
    @abstractmethod
    def extensions(self) -> tuple[str, ...]:
        """Расширения файлов с точкой, например ``('.xml',)``."""

    @abstractmethod
    def split(
        self,
        content: str,
        config: ChunkConfig,
        counter: TokenCounter,
    ) -> list[str]:
        """Разбить содержимое на готовые текстовые чанки того же формата."""
