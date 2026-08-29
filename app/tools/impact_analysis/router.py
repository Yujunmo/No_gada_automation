from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.common.io.sftp import SourceError, SourceReader, default_reader
from app.common.io.ssh import CommandRunner, SshError, default_command_runner
from app.tools.impact_analysis import service
from app.tools.impact_analysis.service import CallerRefType

logger = logging.getLogger("no_gada.impact_analysis")

router = APIRouter(prefix="/impact-analysis")


class DbiosResponse(BaseModel):
    table: str          # 조회한 테이블명(정규화 전 입력 그대로)
    dbios: list[str]    # 그 테이블을 참조하는 DBIO ID 확정 목록(정렬, 파싱 확정됨)


class CallersResponse(BaseModel):
    ref_type: str         # 조회한 참조 타입("dbio" 또는 "biz")
    ref_id: str           # 조회한 ID(정규화 전 입력 그대로)
    services: list[str]  # 이걸 호출하는 service 모듈 확정 목록(정렬)
    bizs: list[str]      # 이걸 호출하는 biz 모듈 확정 목록(정렬)
    batches: list[str]   # 이걸 호출하는 batch 모듈 확정 목록(정렬)


# 부작용 없는 조회라 GET(경로 파라미터). 테이블명은 대문자/영숫자/언더스코어라 세그먼트로 안전.
@router.get("/dbios/{table}", response_model=DbiosResponse)
def find_dbios_by_table(
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


# 부작용 없는 조회라 GET(경로+쿼리 파라미터). ref_type은 dbio/biz만 허용(service/batch는
# 항상 최상위라 "누가 부르나"를 물을 대상이 아님 — CallerRefType 참고). resource_groups는
# 프론트의 업무그룹 필터를 그대로 넘겨받아 grep 범위를 좁힌다(비어 있으면 전체 업무그룹 대상).
@router.get("/callers/{ref_type}/{ref_id}", response_model=CallersResponse)
def find_callers(
    ref_type: CallerRefType,
    ref_id: str,
    resource_groups: list[str] = Query(default=[]),
    searcher: CommandRunner = Depends(default_command_runner),
    reader: SourceReader = Depends(default_reader),
) -> CallersResponse:
    """(참조 타입, ID) → 이걸 호출하는 biz/service/batch 확정 목록(1홉 grep 후보 → 2홉 파싱 확정).

    원격 grep으로 좁힌 후보를 실제 모듈 소스 파싱으로 검증해 오탐을 거른다. DBIO를 펼칠 때도,
    그 결과로 나온 Biz를 다시 펼쳐 상위 호출자를 재귀적으로 따라갈 때도 같은 엔드포인트를 쓴다.
    """
    ident = ref_id.strip()
    logger.info("callers 요청 수신: ref_type=%s ref_id=%s resource_groups=%s", ref_type, ident, resource_groups)

    if not ident:
        logger.warning("callers 거부: 빈 ref_id")
        raise HTTPException(status_code=400, detail="ref_id is empty")

    try:
        found = service.find_callers(ref_type, ident, searcher, reader, resource_groups or None)
    except SshError as e:
        logger.warning("callers 실패(원격 grep): %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except SourceError as e:
        logger.warning("callers 실패(원격 조회): %s", e)
        raise HTTPException(status_code=503, detail=str(e))

    logger.info(
        "callers 완료: ref_type=%s ref_id=%s → service=%d biz=%d batch=%d",
        ref_type, ident, len(found.services), len(found.bizs), len(found.batches),
    )
    return CallersResponse(
        ref_type=ref_type, ref_id=ident,
        services=found.services, bizs=found.bizs, batches=found.batches,
    )
