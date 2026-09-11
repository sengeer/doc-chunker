"""Нарезка JSON-документов на валидные JSON-чанки."""

from __future__ import annotations

import json
from typing import Any

from doc_chunker.config import ChunkConfig
from doc_chunker.protocols import TokenCounter
from doc_chunker.splitters.base import FormatSplitter
from doc_chunker.splitters.structured import split_tree


def dumps(value: Any) -> str:
    """Сериализовать значение компактно, сохраняя Юникод."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class JsonSplitter(FormatSplitter):
    """Делит массивы по элементам, объекты — по ключам."""

    @property
    def extensions(self) -> tuple[str, ...]:
        return (".json",)

    def split_content(
        self,
        content: str,
        config: ChunkConfig,
        counter: TokenCounter,
    ) -> list[str]:
        data = json.loads(content)
        return split_tree(
            data,
            config,
            counter,
            dumps,
            json.loads,
            empty_list=dumps([]),
            empty_dict=dumps({}),
        )
