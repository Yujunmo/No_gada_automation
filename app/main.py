from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.tools.table_extractor.router import router as table_extractor_router
from app.tools.dbio_extractor.router import router as dbio_extractor_router

app = FastAPI(title="No-Gada Auto")

app.include_router(table_extractor_router)
app.include_router(dbio_extractor_router)

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
