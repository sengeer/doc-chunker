"""Нарезка JSON-подобных деревьев (dict/list/скаляры) по бюджету токенов."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from doc_chunker.config import ChunkConfig
from doc_chunker.packing import pack_units, split_oversized_text
from doc_chunker.protocols import TokenCounter

Dumper = Callable[[Any], str]
Loader = Callable[[str], Any]


def _shrink(config: ChunkConfig, overhead: int) -> ChunkConfig:
    """Уменьшить целевой бюджет на стоимость обёртки родительского формата."""
    return ChunkConfig(
        target_tokens=max(1, config.target_tokens - max(0, overhead)),
        max_ratio=config.max_ratio,
        encoding=config.encoding,
    )


def split_tree(
    data: Any,
    config: ChunkConfig,
    counter: TokenCounter,
    dumps: Dumper,
    loads: Loader,
    *,
    empty_list: str = "[]",
    empty_dict: str = "{}",
    join: str = ",",
) -> list[str]:
    """Разбить дерево на валидные документы того же вида (объект или массив)."""
    serialized = dumps(data)
    if counter.count(serialized) <= config.target_tokens:
        return [serialized]

    if isinstance(data, list):
        wrapper_tokens = counter.count(empty_list)
        units = _list_member_units(data, config, counter, dumps, loads, wrapper_tokens)

        def assemble(parts: Sequence[str]) -> str:
            return dumps([loads(part) for part in parts])

        return pack_units(
            units,
            config,
            counter,
            assemble=assemble,
            wrapper_tokens=wrapper_tokens,
            join=join,
        )

    if isinstance(data, dict):
        wrapper_tokens = counter.count(empty_dict)
        units = _dict_member_units(data, config, counter, dumps, loads, wrapper_tokens)

        def assemble(parts: Sequence[str]) -> str:
            merged: dict[str, Any] = {}
            for part in parts:
                _merge_dict(merged, loads(part))
            return dumps(merged)

        return pack_units(
            units,
            config,
            counter,
            assemble=assemble,
            wrapper_tokens=wrapper_tokens,
            join=join,
        )

    if isinstance(data, str):
        quote_overhead = max(0, counter.count(dumps("")) )
        body_budget = max(1, config.max_tokens - quote_overhead)
        return [dumps(piece) for piece in split_oversized_text(data, body_budget, counter)]

    return [serialized]


def _list_member_units(
    items: list[Any],
    config: ChunkConfig,
    counter: TokenCounter,
    dumps: Dumper,
    loads: Loader,
    wrapper_tokens: int,
) -> list[str]:
    body_budget = max(1, config.max_tokens - wrapper_tokens)
    units: list[str] = []
    for item in items:
        dumped = dumps(item)
        if counter.count(dumped) <= body_budget:
            units.append(dumped)
            continue
        units.extend(split_tree(item, _shrink(config, wrapper_tokens), counter, dumps, loads))
    return units


def _dict_member_units(
    data: dict[str, Any],
    config: ChunkConfig,
    counter: TokenCounter,
    dumps: Dumper,
    loads: Loader,
    wrapper_tokens: int,
) -> list[str]:
    body_budget = max(1, config.max_tokens - wrapper_tokens)
    units: list[str] = []
    for key, value in data.items():
        dumped = dumps({key: value})
        if counter.count(dumped) <= body_budget:
            units.append(dumped)
            continue
        if isinstance(value, str):
            key_overhead = counter.count(dumps({key: ""}))
            pieces = split_oversized_text(
                value,
                max(1, body_budget - key_overhead),
                counter,
            )
            units.extend(dumps({key: part}) for part in pieces)
            continue
        if isinstance(value, list):
            units.extend(
                _wrapped_list_units(key, value, config, counter, dumps, loads, body_budget)
            )
            continue
        nested_chunks = split_tree(
            value,
            _shrink(config, wrapper_tokens),
            counter,
            dumps,
            loads,
        )
        for chunk in nested_chunks:
            units.append(dumps({key: loads(chunk)}))
    return units


def _wrapped_list_units(
    key: str,
    items: list[Any],
    config: ChunkConfig,
    counter: TokenCounter,
    dumps: Dumper,
    loads: Loader,
    body_budget: int,
) -> list[str]:
    """Упаковать список как значение ключа, не сериализуя массив корнем документа."""
    units: list[str] = []
    current: list[Any] = []

    def current_dump() -> str:
        return dumps({key: current})

    for item in items:
        candidate = current + [item]
        dumped = dumps({key: candidate})
        if counter.count(dumped) <= body_budget:
            current = candidate
            continue
        if current:
            units.append(current_dump())
            current = []
        one = dumps({key: [item]})
        if counter.count(one) <= body_budget:
            current = [item]
        else:
            units.extend(
                _explode_list_item(key, item, config, counter, dumps, loads, body_budget)
            )
    if current:
        units.append(current_dump())
    return units


def _explode_list_item(
    key: str,
    item: Any,
    config: ChunkConfig,
    counter: TokenCounter,
    dumps: Dumper,
    loads: Loader,
    body_budget: int,
) -> list[str]:
    dumped = dumps({key: [item]})
    if counter.count(dumped) <= body_budget:
        return [dumped]
    if isinstance(item, str):
        overhead = counter.count(dumps({key: [""]}))
        parts = split_oversized_text(item, max(1, body_budget - overhead), counter)
        return [dumps({key: [part]}) for part in parts]
    if isinstance(item, (dict, list)):
        try:
            nested = split_tree(item, config, counter, dumps, loads)
        except TypeError:
            return [dumped]
        result: list[str] = []
        for chunk in nested:
            loaded = loads(chunk)
            wrapped = dumps({key: loaded if isinstance(loaded, list) else [loaded]})
            result.append(wrapped)
        return result
    return [dumped]


def _merge_dict(target: dict[str, Any], piece: dict[str, Any]) -> None:
    """Слить ключи; одноимённые строки и списки склеиваются как продолжение."""
    for key, value in piece.items():
        if key not in target:
            target[key] = value
            continue
        current = target[key]
        if isinstance(current, str) and isinstance(value, str):
            target[key] = current + value
        elif isinstance(current, list) and isinstance(value, list):
            target[key] = current + value
        elif isinstance(current, dict) and isinstance(value, dict):
            _merge_dict(current, value)
        else:
            target[key] = value
