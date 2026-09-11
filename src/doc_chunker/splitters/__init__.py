"""Встроенные стратегии нарезки по форматам."""

from doc_chunker.splitters.csv import CsvSplitter
from doc_chunker.splitters.html import HtmlSplitter
from doc_chunker.splitters.json import JsonSplitter
from doc_chunker.splitters.markdown import MarkdownSplitter
from doc_chunker.splitters.text import TextSplitter
from doc_chunker.splitters.toml import TomlSplitter
from doc_chunker.splitters.xml import XmlSplitter
from doc_chunker.splitters.yaml import YamlSplitter

__all__ = [
    "CsvSplitter",
    "HtmlSplitter",
    "JsonSplitter",
    "MarkdownSplitter",
    "TextSplitter",
    "TomlSplitter",
    "XmlSplitter",
    "YamlSplitter",
]
