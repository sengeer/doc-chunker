"""Семантическая нарезка документов на чанки под контекстное окно LLM."""

from doc_chunker.config import ChunkConfig
from doc_chunker.pipeline import ChunkPipeline
from doc_chunker.tokens import CharTokenCounter, TiktokenTokenCounter

__all__ = [
    "ChunkConfig",
    "ChunkPipeline",
    "CharTokenCounter",
    "TiktokenTokenCounter",
]

__version__ = "1.0.0"
