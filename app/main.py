from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.extractor import ExtractionError, extract_tables

MAX_SQL_BYTES = 1024 * 1024  # 1MB

app = FastAPI(title="Oracle SQL Table Extractor")


class ExtractRequest(BaseModel):
    sql: str


class ExtractResponse(BaseModel):
    tables: list[str]


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest) -> ExtractResponse:
    if len(req.sql.encode("utf-8")) > MAX_SQL_BYTES:
        raise HTTPException(status_code=413, detail="SQL exceeds 1MB limit")
    try:
        tables = extract_tables(req.sql)
    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ExtractResponse(tables=tables)


app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
