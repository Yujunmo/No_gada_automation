from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.tools.sql_bench.router import router as sql_bench_router
from app.tools.table_extractor.router import router as table_extractor_router

# 콘솔 + 회전 파일 양쪽에 로그 기록 (logs/no_gada.log, 5MB x 5개 보관)
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

_log_formatter = logging.Formatter(
    "%(asctime)s %(levelname)s [%(name)s] (%(filename)s:%(lineno)d) %(message)s"
)

_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_log_formatter)

_file_handler = RotatingFileHandler(
    LOG_DIR / "no_gada.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
_file_handler.setFormatter(_log_formatter)

# 루트는 INFO(서드파티 로그 억제), 우리 앱 로거(no_gada.*)만 DEBUG
logging.basicConfig(level=logging.INFO, handlers=[_console_handler, _file_handler])
logging.getLogger("no_gada").setLevel(logging.DEBUG)

app = FastAPI(title="No_Gada")

app.include_router(sql_bench_router)
app.include_router(table_extractor_router)

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
