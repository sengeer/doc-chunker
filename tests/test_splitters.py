"""Тесты форматных splitter-стратегий."""

from __future__ import annotations

import json
import tomllib
import xml.etree.ElementTree as ET

import yaml

from doc_chunker.config import ChunkConfig
from doc_chunker.splitters.csv import CsvSplitter
from doc_chunker.splitters.html import HtmlSplitter
from doc_chunker.splitters.json import JsonSplitter
from doc_chunker.splitters.markdown import MarkdownSplitter
from doc_chunker.splitters.text import TextSplitter
from doc_chunker.splitters.toml import TomlSplitter
from doc_chunker.splitters.xml import XmlSplitter
from doc_chunker.splitters.yaml import YamlSplitter
from doc_chunker.tokens import CharTokenCounter

COUNTER = CharTokenCounter()


def _config(target: int, max_ratio: float = 1.2) -> ChunkConfig:
    return ChunkConfig(target_tokens=target, max_ratio=max_ratio)


def test_json_array_is_split_into_valid_arrays() -> None:
    payload = json.dumps([{"id": index, "text": "item"} for index in range(10)])
    chunks = JsonSplitter().split(payload, _config(40), COUNTER)
    parsed = [json.loads(chunk) for chunk in chunks]
    assert len(chunks) >= 2
    assert all(isinstance(item, list) for item in parsed)
    assert [row["id"] for group in parsed for row in group] == list(range(10))


def test_json_object_is_split_by_keys() -> None:
    payload = json.dumps({f"key{i}": "x" * 12 for i in range(6)}, ensure_ascii=False)
    chunks = JsonSplitter().split(payload, _config(30), COUNTER)
    assert len(chunks) >= 2
    merged: dict[str, str] = {}
    for chunk in chunks:
        piece = json.loads(chunk)
        assert isinstance(piece, dict)
        merged.update(piece)
    assert set(merged) == {f"key{i}" for i in range(6)}


def test_xml_generic_children_stay_well_formed() -> None:
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<root>"
        "<item>alpha</item><item>bravo</item><item>charlie</item>"
        "</root>"
    )
    chunks = XmlSplitter().split(content, _config(80), COUNTER)
    assert len(chunks) >= 2
    for chunk in chunks:
        root = ET.fromstring(chunk.encode("utf-8"))
        assert root.tag == "root"
        assert list(root)


def test_word_xml_keeps_document_wrapper() -> None:
    content = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p><w:r><w:t>Первый абзац текста</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>Второй абзац текста</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>Третий абзац текста</w:t></w:r></w:p>"
        '<w:sectPr><w:type w:val="nextPage"/></w:sectPr>'
        "</w:body></w:document>"
    )
    chunks = XmlSplitter().split(content, _config(280), COUNTER)
    assert len(chunks) >= 2
    for chunk in chunks:
        root = ET.fromstring(chunk.encode("utf-8"))
        assert root.tag.endswith("document")
        assert "Первый" in chunks[0] or "абзац" in chunks[0]


def test_yaml_and_toml_and_csv() -> None:
    yaml_text = "a: " + "alpha " * 20 + "\nb: " + "bravo " * 20 + "\n"
    yaml_chunks = YamlSplitter().split(yaml_text, _config(50), COUNTER)
    assert len(yaml_chunks) >= 2
    for chunk in yaml_chunks:
        assert yaml.safe_load(chunk)

    toml_text = 'title = "doc"\n\n[alpha]\ntext = "' + ("hello " * 15) + '"\n\n[beta]\ntext = "' + ("world " * 15) + '"\n'
    toml_chunks = TomlSplitter().split(toml_text, _config(60), COUNTER)
    assert len(toml_chunks) >= 2
    for chunk in toml_chunks:
        tomllib.loads(chunk)

    csv_text = "id,name\n" + "".join(f"{i},name-{i}\n" for i in range(20))
    csv_chunks = CsvSplitter().split(csv_text, _config(40), COUNTER)
    assert len(csv_chunks) >= 2
    for chunk in csv_chunks:
        first_line = chunk.splitlines()[0]
        assert first_line.startswith("id")


def test_html_markdown_text_split_semantically() -> None:
    html = "<html><body><p>Первый блок текста</p><p>Второй блок текста</p><p>Третий блок</p></body></html>"
    html_chunks = HtmlSplitter().split(html, _config(55), COUNTER)
    assert len(html_chunks) >= 2
    assert all("<p>" in chunk for chunk in html_chunks)

    markdown = "# One\n\n" + ("alpha " * 12) + "\n\n# Two\n\n" + ("beta " * 12) + "\n"
    md_chunks = MarkdownSplitter().split(markdown, _config(40), COUNTER)
    assert len(md_chunks) >= 2
    assert md_chunks[0].lstrip().startswith("# One")
    assert any(chunk.lstrip().startswith("# Two") for chunk in md_chunks[1:])

    text = "first paragraph\n\n" + ("word " * 20) + "\n\nsecond paragraph\n\n" + ("log " * 20)
    text_chunks = TextSplitter().split(text, _config(40), COUNTER)
    assert len(text_chunks) >= 2
    assert "".join(text_chunks) == text


def test_small_file_stays_single_chunk() -> None:
    content = '{"ok": true}'
    chunks = JsonSplitter().split(content, _config(1000), COUNTER)
    assert chunks == [content] or json.loads(chunks[0]) == {"ok": True}
