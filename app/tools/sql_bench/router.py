from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.common.sql import ExtractionError, extract_tables

logger = logging.getLogger("no_gada.sql_bench")

MAX_SQL_BYTES = 1024 * 1024  # 1MB

router = APIRouter(prefix="/sql-bench")


class ExtractRequest(BaseModel):
    sql: str


class ExtractResponse(BaseModel):
    tables: list[str]


@router.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest) -> ExtractResponse:
    sql_bytes = len(req.sql.encode("utf-8"))
    logger.info("extract 요청 수신: %d bytes", sql_bytes)

    if sql_bytes > MAX_SQL_BYTES:
        logger.warning("extract 거부: 크기 초과 (%d bytes > %d)", sql_bytes, MAX_SQL_BYTES)
        raise HTTPException(status_code=413, detail="SQL exceeds 1MB limit")

    try:
        tables = extract_tables(req.sql)
    except ExtractionError as e:
        logger.warning("extract 실패: %s", e)
        raise HTTPException(status_code=400, detail=str(e))

    logger.info("extract 완료: %d개 테이블 %s", len(tables), tables)
    return ExtractResponse(tables=tables)
