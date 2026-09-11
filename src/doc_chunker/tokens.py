"""Подсчёт токенов: tiktoken для продакшена и символьный счётчик для тестов."""

from __future__ import annotations

from collections.abc import Sequence

import tiktoken


class TiktokenTokenCounter:
    """BPE-счётчик на кодировке tiktoken (по умолчанию cl100k_base)."""

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        self._encoding_name = encoding_name
        self._encoding = tiktoken.get_encoding(encoding_name)

    @property
    def encoding_name(self) -> str:
        """Имя активной кодировки tiktoken."""
        return self._encoding_name

    def count(self, text: str) -> int:
        """Вернуть число BPE-токенов без специальных токенов модели."""
        return len(self.encode(text))

    def encode(self, text: str) -> list[int]:
        """Закодировать текст; спецтокены в документе не считаются ошибкой."""
        return self._encoding.encode(text, disallowed_special=())

    def decode(self, tokens: Sequence[int]) -> str:
        """Собрать текст из идентификаторов токенов."""
        return self._encoding.decode(list(tokens))


class CharTokenCounter:
    """Тестовый счётчик: один символ равен одному токену."""

    def count(self, text: str) -> int:
        """Вернуть длину строки в символах."""
        return len(text)

    def encode(self, text: str) -> list[int]:
        """Код каждого символа — отдельный «токен»."""
        return [ord(char) for char in text]

    def decode(self, tokens: Sequence[int]) -> str:
        """Собрать строку из кодов символов."""
        return "".join(chr(token) for token in tokens)
