"""Нарезка TOML по ключам верхнего уровня."""

from __future__ import annotations

import tomllib
from typing import Any

import tomli_w

from doc_chunker.config import ChunkConfig
from doc_chunker.protocols import TokenCounter
from doc_chunker.splitters.base import FormatSplitter
from doc_chunker.splitters.structured import split_tree


def dumps(value: Any) -> str:
    """Сериализовать таблицу в TOML."""
    if not isinstance(value, dict):
        raise TypeError("Корень TOML должен быть таблицей (dict)")
    return tomli_w.dumps(value)


class TomlSplitter(FormatSplitter):
    """Делит TOML-таблицу по ключам, сохраняя валидность каждого чанка."""

    @property
    def extensions(self) -> tuple[str, ...]:
        return (".toml",)

    def split_content(
        self,
        content: str,
        config: ChunkConfig,
        counter: TokenCounter,
    ) -> list[str]:
        data = tomllib.loads(content)
        return split_tree(
            data,
            config,
            counter,
            dumps,
            tomllib.loads,
            empty_dict=dumps({}),
        )
