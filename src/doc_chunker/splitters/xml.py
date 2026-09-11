"""Нарезка XML, включая WordprocessingML (OOXML)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from xml.etree.ElementTree import Element

from doc_chunker.config import ChunkConfig
from doc_chunker.packing import pack_units
from doc_chunker.protocols import TokenCounter
from doc_chunker.splitters.base import FormatSplitter

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W_DOCUMENT = f"{{{W_NS}}}document"
W_BODY = f"{{{W_NS}}}body"
W_SECTPR = f"{{{W_NS}}}sectPr"

_XMLNS_PREFIX = re.compile(r'xmlns:([A-Za-z0-9_]+)="([^"]*)"')
_XMLNS_DEFAULT = re.compile(r'(?:^|[\s])xmlns="([^"]*)"')
_XML_DECL = re.compile(r"^\s*(<\?xml[^?]*\?>\s*)?", re.ASCII)


class XmlSplitter(FormatSplitter):
    """Делит XML по дочерним элементам корня (для Word — по детям ``w:body``)."""

    @property
    def extensions(self) -> tuple[str, ...]:
        return (".xml",)

    def split_content(
        self,
        content: str,
        config: ChunkConfig,
        counter: TokenCounter,
    ) -> list[str]:
        root = ET.fromstring(content.encode("utf-8"))
        nsmap = _namespace_map(content)
        if _is_word_document(root):
            return self._split_word(content, root, nsmap, config, counter)
        return self._split_generic(content, root, nsmap, config, counter)

    def _split_word(
        self,
        content: str,
        root: Element,
        nsmap: dict[str, str],
        config: ChunkConfig,
        counter: TokenCounter,
    ) -> list[str]:
        body = root.find(W_BODY)
        if body is None:
            return self._split_generic(content, root, nsmap, config, counter)

        prefix, suffix = _word_wrapper(content)
        wrapper_tokens = counter.count(prefix + suffix)
        with registered_namespaces(nsmap):
            units = [
                ET.tostring(child, encoding="unicode")
                for child in list(body)
                if child.tag != W_SECTPR
            ]
        return _pack_wrapped(units, prefix, suffix, wrapper_tokens, config, counter)

    def _split_generic(
        self,
        content: str,
        root: Element,
        nsmap: dict[str, str],
        config: ChunkConfig,
        counter: TokenCounter,
    ) -> list[str]:
        prefix, suffix = _generic_wrapper(content)
        wrapper_tokens = counter.count(prefix + suffix)
        with registered_namespaces(nsmap):
            units = list(_iter_root_units(root))
        if not units:
            return [content]
        return _pack_wrapped(units, prefix, suffix, wrapper_tokens, config, counter)


def _pack_wrapped(
    units: Sequence[str],
    prefix: str,
    suffix: str,
    wrapper_tokens: int,
    config: ChunkConfig,
    counter: TokenCounter,
) -> list[str]:
    if counter.count(prefix + "".join(units) + suffix) <= config.target_tokens:
        return [prefix + "".join(units) + suffix]

    def assemble(parts: Sequence[str]) -> str:
        return prefix + "".join(parts) + suffix

    return pack_units(
        units,
        config,
        counter,
        assemble=assemble,
        wrapper_tokens=wrapper_tokens,
        join="",
        split_oversized=_keep_xml_unit,
    )


def _keep_xml_unit(text: str, max_tokens: int, counter: TokenCounter) -> list[str]:
    """Не резать XML-элемент по символам: лучше чуть превысить бюджет, чем сломать разметку."""
    del max_tokens, counter
    return [text]


def _is_word_document(root: Element) -> bool:
    return root.tag == W_DOCUMENT or (
        root.tag.endswith("}document") and "wordprocessingml" in root.tag
    )


def _word_wrapper(content: str) -> tuple[str, str]:
    body_open = re.search(r"<w:body(?:\s[^>]*)?>", content)
    if body_open is None:
        raise ValueError("Word XML: не найден элемент w:body")
    prefix = content[: body_open.end()]
    body_close = content.rfind("</w:body>")
    if body_close < 0:
        raise ValueError("Word XML: не найден закрывающий тег w:body")
    sect = content.rfind("<w:sectPr")
    if 0 <= sect < body_close:
        return prefix, content[sect:]
    return prefix, content[body_close:]


def _generic_wrapper(content: str) -> tuple[str, str]:
    decl = _XML_DECL.match(content)
    start = decl.end() if decl else 0
    open_match = re.match(r"<([A-Za-z0-9:_]+)([^>]*)>", content[start:])
    if open_match is None:
        raise ValueError("XML: не найден корневой элемент")
    tag_name = open_match.group(1)
    prefix = content[: start + open_match.end()]
    close = f"</{tag_name}>"
    close_at = content.rfind(close)
    if close_at < 0:
        return prefix, ""
    return prefix, content[close_at:]


def _iter_root_units(root: Element) -> Iterator[str]:
    if root.text and root.text.strip():
        yield root.text
    for child in list(root):
        yield ET.tostring(child, encoding="unicode")
        if child.tail and child.tail.strip():
            yield child.tail


def _namespace_map(xml_head: str) -> dict[str, str]:
    head = xml_head[:8000]
    mapping = {prefix: uri for prefix, uri in _XMLNS_PREFIX.findall(head)}
    default = _XMLNS_DEFAULT.search(head)
    if default:
        mapping[""] = default.group(1)
    return mapping


@contextmanager
def registered_namespaces(nsmap: dict[str, str]) -> Iterator[None]:
    """Временно зарегистрировать префиксы xmlns для сериализации ElementTree."""
    original = dict(ET._namespace_map)
    try:
        for prefix, uri in nsmap.items():
            ET.register_namespace(prefix, uri)
        yield
    finally:
        ET._namespace_map.clear()
        ET._namespace_map.update(original)
