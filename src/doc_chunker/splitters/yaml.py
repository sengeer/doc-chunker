"""Нарезка YAML, включая многодокументные файлы."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import yaml

from doc_chunker.config import ChunkConfig
from doc_chunker.packing import pack_units
from doc_chunker.protocols import TokenCounter
from doc_chunker.splitters.base import FormatSplitter
from doc_chunker.splitters.structured import split_tree


def dumps(value: Any) -> str:
    """Сериализовать значение в YAML без сортировки ключей."""
    return yaml.safe_dump(value, allow_unicode=True, sort_keys=False)


class YamlSplitter(FormatSplitter):
    """Сначала режет по документам ``---``, затем по структуре каждого документа."""

    @property
    def extensions(self) -> tuple[str, ...]:
        return (".yaml", ".yml")

    def split_content(
        self,
        content: str,
        config: ChunkConfig,
        counter: TokenCounter,
    ) -> list[str]:
        documents = list(yaml.safe_load_all(content))
        documents = [doc for doc in documents if doc is not None]
        if not documents:
            return [content]

        tree_kwargs = {
            "empty_list": dumps([]),
            "empty_dict": dumps({}),
        }
        if len(documents) == 1:
            return split_tree(
                documents[0],
                config,
                counter,
                dumps,
                yaml.safe_load,
                **tree_kwargs,
            )

        units: list[str] = []
        for document in documents:
            units.extend(
                split_tree(
                    document,
                    config,
                    counter,
                    dumps,
                    yaml.safe_load,
                    **tree_kwargs,
                )
            )

        wrapper_tokens = counter.count("---\n")
        join = "---\n"

        def assemble(parts: Sequence[str]) -> str:
            body = "\n---\n".join(part.strip() for part in parts)
            if not body.endswith("\n"):
                body += "\n"
            return body

        packed = pack_units(
            units,
            config,
            counter,
            assemble=assemble,
            wrapper_tokens=wrapper_tokens,
            join=join,
        )
        return packed
