"""Тесты конфигурации бюджета токенов."""

import pytest

from doc_chunker.config import ChunkConfig


def test_from_size_k_uses_1024_tokens() -> None:
    config = ChunkConfig.from_size_k(16)
    assert config.target_tokens == 16 * 1024
    assert config.max_tokens == int(16384 * 1.2)


def test_rejects_invalid_size() -> None:
    with pytest.raises(ValueError):
        ChunkConfig.from_size_k(0)
    with pytest.raises(ValueError):
        ChunkConfig(target_tokens=10, max_ratio=0.9)
