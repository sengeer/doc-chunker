"""Тесты жадной упаковки и нарезки oversized-единиц."""

from collections.abc import Sequence

from doc_chunker.config import ChunkConfig
from doc_chunker.packing import pack_units, split_oversized_text
from doc_chunker.tokens import CharTokenCounter


def _join(parts: Sequence[str]) -> str:
    return "".join(parts)


def test_pack_stays_near_target() -> None:
    counter = CharTokenCounter()
    config = ChunkConfig(target_tokens=10, max_ratio=1.2)
    chunks = pack_units(
        ["aaaa", "bbbb", "cccc", "dddd"],
        config,
        counter,
        assemble=_join,
        wrapper_tokens=0,
        join="",
    )
    assert chunks == ["aaaabbbbcccc", "dddd"]
    assert all(counter.count(chunk) <= config.max_tokens for chunk in chunks)


def test_pack_allows_semantic_overflow() -> None:
    counter = CharTokenCounter()
    config = ChunkConfig(target_tokens=10, max_ratio=1.2)
    chunks = pack_units(
        ["aaaaaaaaaa", "bb"],
        config,
        counter,
        assemble=_join,
        wrapper_tokens=0,
    )
    assert chunks[0] == "aaaaaaaaaabb"
    assert counter.count(chunks[0]) <= config.max_tokens


def test_pack_includes_wrapper_tokens() -> None:
    counter = CharTokenCounter()
    config = ChunkConfig(target_tokens=10, max_ratio=1.0)

    def assemble(parts: Sequence[str]) -> str:
        return f"<>{''.join(parts)}</>"

    chunks = pack_units(
        ["aaa", "bbb", "ccc"],
        config,
        counter,
        assemble=assemble,
        wrapper_tokens=counter.count("<></>"),
    )
    assert all(chunk.startswith("<>") and chunk.endswith("</>") for chunk in chunks)
    assert all(counter.count(chunk) <= config.max_tokens for chunk in chunks)
    assert len(chunks) >= 2


def test_oversized_unit_is_split_and_reconstructed() -> None:
    counter = CharTokenCounter()
    text = "one. two. three. four."
    pieces = split_oversized_text(text, max_tokens=8, counter=counter)
    assert "".join(pieces) == text
    assert all(counter.count(piece) <= 8 for piece in pieces)


def test_split_by_tokens_for_unseparated_text() -> None:
    counter = CharTokenCounter()
    pieces = split_oversized_text("abcdefghij", max_tokens=4, counter=counter)
    assert "".join(pieces) == "abcdefghij"
    assert all(len(piece) <= 4 for piece in pieces)
