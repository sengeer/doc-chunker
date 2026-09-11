"""HTTP API для запуска нарезки из Docker / n8n."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from doc_chunker.config import DEFAULT_ENCODING, DEFAULT_MAX_RATIO, ChunkConfig
from doc_chunker.pipeline import ChunkPipeline
from doc_chunker.tokens import TiktokenTokenCounter

app = FastAPI(
    title="doc-chunker",
    description="Семантическая нарезка документов под контекстное окно LLM.",
    version="1.0.0",
)


class ChunkRequest(BaseModel):
    """Параметры одного прогона нарезки."""

    size: int = Field(default=16, ge=1, description="Окно в тысячах токенов: 16 → 16384.")
    input_dir: str = Field(default="/data/input", description="Папка с исходниками.")
    output_dir: str = Field(default="/data/output", description="Папка для чанков.")
    encoding: str = Field(default=DEFAULT_ENCODING)
    max_ratio: float = Field(default=DEFAULT_MAX_RATIO, ge=1.0)
    clear_output: bool = Field(
        default=True,
        description="Удалить файлы в output_dir перед нарезкой.",
    )


class ChunkResponse(BaseModel):
    """Результат нарезки."""

    ok: bool
    files: list[str]
    messages: list[str]
    count: int


@app.get("/health")
def health() -> dict[str, str]:
    """Проверка живости контейнера."""
    return {"status": "ok"}


@app.post("/chunk", response_model=ChunkResponse)
def chunk(req: ChunkRequest) -> ChunkResponse:
    """Нарезать все поддерживаемые файлы из input_dir в output_dir."""
    input_dir = Path(req.input_dir)
    output_dir = Path(req.output_dir)

    if not input_dir.is_dir():
        raise HTTPException(status_code=400, detail=f"input_dir не найден: {input_dir}")

    try:
        config = ChunkConfig.from_size_k(
            req.size,
            max_ratio=req.max_ratio,
            encoding=req.encoding,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    output_dir.mkdir(parents=True, exist_ok=True)
    if req.clear_output:
        for path in output_dir.iterdir():
            if path.is_file() and not path.name.startswith("."):
                path.unlink()

    messages: list[str] = []
    counter = TiktokenTokenCounter(req.encoding)
    pipeline = ChunkPipeline(config, counter, on_message=messages.append)

    try:
        written = pipeline.run(input_dir, output_dir)
    except Exception as error:  # noqa: BLE001 — наружу как HTTP 500
        raise HTTPException(status_code=500, detail=str(error)) from error

    files = [path.name for path in written]
    return ChunkResponse(ok=True, files=files, messages=messages, count=len(files))
