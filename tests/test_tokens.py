"""Тесты счётчиков токенов."""

from doc_chunker.tokens import CharTokenCounter, TiktokenTokenCounter


def test_char_counter_roundtrip() -> None:
    counter = CharTokenCounter()
    text = "привет"
    assert counter.count(text) == len(text)
    assert counter.decode(counter.encode(text)) == text


def test_tiktoken_counts_real_tokens() -> None:
    counter = TiktokenTokenCounter("cl100k_base")
    text = "hello world"
    tokens = counter.encode(text)
    assert len(tokens) == counter.count(text)
    assert len(tokens) >= 2
    assert counter.decode(tokens) == text
