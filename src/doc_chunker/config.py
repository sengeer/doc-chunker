"""Конфигурация размера чанка в токенах."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_ENCODING = "cl100k_base"
DEFAULT_MAX_RATIO = 1.2
TOKENS_PER_K = 1024


@dataclass(frozen=True, slots=True)
class ChunkConfig:
    """Параметры нарезки: целевой бюджет токенов и допустимый выход за него.

    Attributes:
        target_tokens: Целевой размер чанка в токенах (для ``--size 16`` это 16384).
        max_ratio: Множитель мягкого лимита, чтобы не резать семантическую единицу.
        encoding: Имя BPE-кодировки tiktoken.
    """

    target_tokens: int
    max_ratio: float = DEFAULT_MAX_RATIO
    encoding: str = DEFAULT_ENCODING

    def __post_init__(self) -> None:
        if self.target_tokens < 1:
            raise ValueError("target_tokens должен быть >= 1")
        if self.max_ratio < 1.0:
            raise ValueError("max_ratio должен быть >= 1.0")

    @property
    def max_tokens(self) -> int:
        """Жёсткий потолок с учётом семантического переполнения."""
        return max(self.target_tokens, int(self.target_tokens * self.max_ratio))

    @classmethod
    def from_size_k(
        cls,
        size: int,
        *,
        max_ratio: float = DEFAULT_MAX_RATIO,
        encoding: str = DEFAULT_ENCODING,
    ) -> ChunkConfig:
        """Собрать конфиг из обозначения окна LLM: ``16`` → 16K = 16384 токена."""
        if size < 1:
            raise ValueError("size должен быть >= 1")
        return cls(
            target_tokens=size * TOKENS_PER_K,
            max_ratio=max_ratio,
            encoding=encoding,
        )
