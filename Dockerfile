FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir ".[api]" \
    && mkdir -p /data/input /data/output

EXPOSE 8091

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8091/health')"

CMD ["uvicorn", "doc_chunker.api:app", "--host", "0.0.0.0", "--port", "8091"]
