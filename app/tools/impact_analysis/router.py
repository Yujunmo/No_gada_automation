from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.common.io.sftp import SourceError, SourceReader, default_reader
from app.common.io.ssh import CommandRunner, SshError, default_command_runner
from app.tools.impact_analysis import service

logger = logging.getLogger("no_gada.impact_analysis")

router = APIRouter(prefix="/impact-analysis")


class DbiosResponse(BaseModel):
    table: str          # 조회한 테이블명(정규화 전 입력 그대로)
    dbios: list[str]    # 그 테이블을 참조하는 DBIO ID 확정 목록(정렬, 파싱 확정됨)


# 부작용 없는 조회라 GET(경로 파라미터). 테이블명은 대문자/영숫자/언더스코어라 세그먼트로 안전.
@router.get("/dbios/{table}", response_model=DbiosResponse)
def dbios(
    table: str,
    searcher: CommandRunner = Depends(default_command_runner),
    reader: SourceReader = Depends(default_reader),
) -> DbiosResponse:
    """테이블 → 그 테이블을 참조하는 DBIO 확정 목록(1홉 grep 후보 → 2홉 파싱 확정).

    원격 grep으로 좁힌 후보를 실제 DBIO XML 파싱으로 검증해 오탐을 거른다.
    """
    ident = table.strip()
    logger.info("dbios 요청 수신: table=%s", ident)

    if not ident:
        logger.warning("dbios 거부: 빈 테이블명")
        raise HTTPException(status_code=400, detail="table is empty")

    try:
        found = service.find_dbios(ident, searcher, reader)
    except SshError as e:
        logger.warning("dbios 실패(원격 grep): %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except SourceError as e:
        logger.warning("dbios 실패(원격 조회): %s", e)
        raise HTTPException(status_code=503, detail=str(e))

    logger.info("dbios 완료: table=%s → %d개", ident, len(found))
    return DbiosResponse(table=ident, dbios=found)
