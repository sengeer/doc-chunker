"""Оркестрация: файлы из input/ в нумерованные чанки output/."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from doc_chunker.config import ChunkConfig
from doc_chunker.protocols import TokenCounter
from doc_chunker.registry import SplitterRegistry

ProgressCallback = Callable[[str], None]


class ChunkPipeline:
    """Обходит входную папку, режет каждый поддерживаемый файл, пишет чанки."""

    def __init__(
        self,
        config: ChunkConfig,
        counter: TokenCounter,
        registry: SplitterRegistry | None = None,
        *,
        on_message: ProgressCallback | None = None,
    ) -> None:
        self._config = config
        self._counter = counter
        self._registry = registry or SplitterRegistry.default()
        self._on_message = on_message or (lambda _message: None)

    def run(self, input_dir: Path, output_dir: Path) -> list[Path]:
        """Обработать все файлы в ``input_dir`` и вернуть пути записанных чанков."""
        if not input_dir.is_dir():
            raise FileNotFoundError(f"Папка input не найдена: {input_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

        written: list[Path] = []
        for path in sorted(input_dir.iterdir()):
            if not path.is_file() or path.name.startswith("."):
                continue
            written.extend(self._process_file(path, output_dir))
        return written

    def _process_file(self, path: Path, output_dir: Path) -> list[Path]:
        splitter = self._registry.get(path.suffix)
        if splitter is None:
            supported = ", ".join(self._registry.supported_extensions())
            self._on_message(
                f"Пропуск {path.name}: неподдерживаемый формат "
                f"(ожидаются {supported})"
            )
            return []

        try:
            content = path.read_text(encoding="utf-8")
            chunks = splitter.split(content, self._config, self._counter)
        except (OSError, UnicodeDecodeError, Exception) as error:
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                raise
            self._on_message(f"Ошибка {path.name}: {error}")
            return []
        written: list[Path] = []
        for index, chunk in enumerate(chunks, start=1):
            target = output_dir / f"{path.stem}_{index}{path.suffix}"
            target.write_text(chunk, encoding="utf-8")
            written.append(target)
        self._on_message(f"{path.name} → {len(chunks)} чанк(ов)")
        return written
