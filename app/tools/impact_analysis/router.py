from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.common.io.ssh import CommandRunner, SshError, default_command_runner
from app.tools.impact_analysis import service

logger = logging.getLogger("no_gada.impact_analysis")

router = APIRouter(prefix="/impact-analysis")


class DbiosResponse(BaseModel):
    table: str          # 조회한 테이블명(정규화 전 입력 그대로)
    dbios: list[str]    # 그 테이블을 참조하는 DBIO ID 후보(정렬, grep 후보 — 확정 아님)


# 부작용 없는 조회라 GET(경로 파라미터). 테이블명은 대문자/영숫자/언더스코어라 세그먼트로 안전.
@router.get("/dbios/{table}", response_model=DbiosResponse)
def dbios(
    table: str,
    searcher: CommandRunner = Depends(default_command_runner),
) -> DbiosResponse:
    """테이블 → 그 테이블을 참조하는 DBIO 후보(Impact Analysis 1홉의 후보 단계).

    원격 grep으로 좁힌 느슨한 후보다(놓침 0 우선, 오탐은 후속 파싱 확정에서 거름).
    """
    ident = table.strip()
    logger.info("dbios 요청 수신: table=%s", ident)

    if not ident:
        logger.warning("dbios 거부: 빈 테이블명")
        raise HTTPException(status_code=400, detail="table is empty")

    try:
        found = service.find_dbios(ident, searcher)
    except SshError as e:
        logger.warning("dbios 실패(원격 grep): %s", e)
        raise HTTPException(status_code=503, detail=str(e))

    logger.info("dbios 완료: table=%s → %d개", ident, len(found))
    return DbiosResponse(table=ident, dbios=found)
