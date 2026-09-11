"""Запуск ``python -m doc_chunker``."""

from __future__ import annotations

import sys

from doc_chunker.cli import main

if __name__ == "__main__":
    sys.exit(main())
