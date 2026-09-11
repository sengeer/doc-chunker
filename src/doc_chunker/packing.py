"""Жадная упаковка семантических единиц в чанки по бюджету токенов.

Сложность: O(n) по суммарной длине единиц плюс O(u) по их числу.
Bin-packing не используем: порядок единиц сохраняется (продолжение документа).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from doc_chunker.config import ChunkConfig
from doc_chunker.protocols import TokenCounter

SEPARATORS: tuple[str, ...] = (
    "\n\n",
    "\n",
    ". ",
    "? ",
    "! ",
    "; ",
    ", ",
    " ",
)


def split_oversized_text(
    text: str,
    max_tokens: int,
    counter: TokenCounter,
) -> list[str]:
    """Рекурсивно нарезать слишком длинную единицу по убывающим разделителям.

    Последний уровень — нарезка по границам токенов через encode/decode, O(n).
    """
    if max_tokens < 1:
        max_tokens = 1
    if not text:
        return [text]
    if counter.count(text) <= max_tokens:
        return [text]

    for separator in SEPARATORS:
        if separator not in text:
            continue
        raw_parts = text.split(separator)
        if len(raw_parts) <= 1:
            continue
        parts = [part + separator for part in raw_parts[:-1]]
        parts.append(raw_parts[-1])
        parts = [part for part in parts if part]
        packed = _pack_plain_parts(parts, "", max_tokens, counter)
        if len(packed) == 1 and packed[0] == text:
            continue
        result: list[str] = []
        progressed = False
        for piece in packed:
            if piece == text:
                continue
            progressed = True
            if counter.count(piece) <= max_tokens:
                result.append(piece)
            else:
                result.extend(split_oversized_text(piece, max_tokens, counter))
        if progressed and result:
            return result

    return _split_by_tokens(text, max_tokens, counter)


def _pack_plain_parts(
    parts: Sequence[str],
    separator: str,
    max_tokens: int,
    counter: TokenCounter,
) -> list[str]:
    """Склеить части с ``separator``, не превышая ``max_tokens``."""
    if not parts:
        return []
    chunks: list[str] = []
    current = parts[0]
    for part in parts[1:]:
        candidate = f"{current}{separator}{part}"
        if counter.count(candidate) <= max_tokens:
            current = candidate
        else:
            chunks.append(current)
            current = part
    chunks.append(current)
    return chunks


def _split_by_tokens(
    text: str,
    max_tokens: int,
    counter: TokenCounter,
) -> list[str]:
    """Нарезать текст ровно по идентификаторам токенов."""
    token_ids = list(counter.encode(text))
    if not token_ids:
        return [text]
    pieces: list[str] = []
    for start in range(0, len(token_ids), max_tokens):
        pieces.append(counter.decode(token_ids[start : start + max_tokens]))
    return pieces or [text]


def pack_units(
    units: Sequence[str],
    config: ChunkConfig,
    counter: TokenCounter,
    *,
    assemble: Callable[[Sequence[str]], str],
    wrapper_tokens: int = 0,
    join: str = "",
    split_oversized: Callable[[str, int, TokenCounter], list[str]] | None = None,
    starts_new_chunk: Callable[[str], bool] | None = None,
) -> list[str]:
    """Упаковать единицы слева направо, учитывая токены обёртки формата.

    Args:
        units: Семантические фрагменты в исходном порядке.
        config: Целевой и максимальный бюджет токенов.
        counter: Счётчик токенов.
        assemble: Сборка готового документа из выбранных единиц.
        wrapper_tokens: Токены префикса/суффикса формата (namespaces, скобки).
        join: Строка между единицами; её токены умножаются на (n-1).
        split_oversized: Нарезка единицы, которая сама больше мягкого лимита.
        starts_new_chunk: Если True, текущий чанк закрывается перед этой единицей.

    Returns:
        Список готовых чанков-документов.
    """
    splitter = split_oversized or split_oversized_text
    expanded: list[str] = []
    for unit in units:
        standalone = assemble([unit])
        if counter.count(standalone) <= config.max_tokens:
            expanded.append(unit)
            continue
        body_budget = max(1, config.max_tokens - wrapper_tokens)
        pieces = splitter(unit, body_budget, counter)
        expanded.extend(pieces or [unit])

    if not expanded:
        assembled = assemble([])
        return [assembled] if assembled else [""]

    join_tokens = counter.count(join) if join else 0
    chunks: list[str] = []
    current: list[str] = []
    current_units_tokens = 0

    def cost(units_tokens: int, count: int) -> int:
        extra_joins = join_tokens * max(0, count - 1)
        return wrapper_tokens + units_tokens + extra_joins

    for unit in expanded:
        unit_tokens = counter.count(unit)
        if current and starts_new_chunk and starts_new_chunk(unit):
            chunks.append(assemble(current))
            current = []
            current_units_tokens = 0
        if not current:
            current = [unit]
            current_units_tokens = unit_tokens
            continue

        new_count = len(current) + 1
        new_tokens = current_units_tokens + unit_tokens
        new_cost = cost(new_tokens, new_count)

        if new_cost <= config.target_tokens or new_cost <= config.max_tokens:
            current.append(unit)
            current_units_tokens = new_tokens
            continue

        chunks.append(assemble(current))
        current = [unit]
        current_units_tokens = unit_tokens

    if current:
        chunks.append(assemble(current))
    return chunks
