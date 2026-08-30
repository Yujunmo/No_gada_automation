from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from typing import Literal, Optional

from app.common.io.db import DbClient, DbError, QueryError, default_db
from app.common.io.sftp import SourceError, SourceNotFound, SourceReader, default_reader
from app.common.parse.sql import ExtractionError
from app.common.proframe import Module_Type, ResourceGroup
from app.common.proframe import db_schema
from app.common.proframe.dbio import UnknownSqlType
from app.tools.data_migration import migrate, service
from app.tools.data_migration.excludes import (
    load_excluded_refs,
    load_excluded_tables,
    save_excluded_refs,
    save_excluded_tables,
)

logger = logging.getLogger("no_gada.data_migration")

router = APIRouter(prefix="/data-migration")


class ExtractResponse(BaseModel):
    tables: list[str]    # 정렬된 대문자 물리 테이블명 합집합
    sql: str             # 수집한 SQL(우측 패널 표시용, ;로 연결)
    dbios: list[str]     # 해석 과정에서 도달한 DBIO ID 목록(참고용)
    batches: list[str]   # 참조만 되고 소스는 들여다보지 않은 배치 ID 목록(참고용)
    services: list[str]  # 재귀 중 실제로 읽어들인 service 모듈 ID(진입 모듈 포함, 추출근거 표시용)
    bizs: list[str]      # 재귀 중 실제로 읽어들인 biz 모듈 ID(진입 모듈 포함, 추출근거 표시용)


MAX_BATCH_FILE_IDS = 50  # SFTP 재귀 탐색이 ID마다 새로 도는 구조라 상한을 둔다


class BatchExtractRequest(BaseModel):
    resource_group: Optional[ResourceGroup] = None  # dbio에서는 생략, 그 외 타입은 필수(라우터에서 검증)
    file_ids: list[str]                              # 여러 ID(프론트가 쉼표로 파싱한 목록, 순서 보존)


class BatchFailedItem(BaseModel):
    file_id: str
    error: str


class BatchExtractResponse(BaseModel):
    tables: list[str]
    sql: str
    dbios: list[str]
    batches: list[str]
    services: list[str]
    bizs: list[str]
    succeeded: list[str]
    failed: list[BatchFailedItem]


class PkRequest(BaseModel):
    tables: list[str]  # PK를 조회할 테이블명 목록(프론트가 정리한 최종 목록)


class PkResponse(BaseModel):
    # {테이블명: [PK 컬럼, ...]} — 요청한 모든 테이블 포함(딕셔너리에 없으면 [])
    pks: dict[str, list[str]]


class KeyCondIn(BaseModel):
    op: Literal["eq", "between"] = "eq"  # 단일=eq, 기간=between
    value: str = ""                       # op=eq일 때
    start: str = ""                       # op=between일 때
    end: str = ""


class MigrateRequest(BaseModel):
    tables: list[str]                     # 이관 대상 테이블(프론트의 필터된 목록)
    from_link: str = ""                   # SELECT 소스(원격지) DB 링크(선택)
    to_link: str = ""                     # DELETE/INSERT 대상 DB 링크(선택, 비우면 로컬)
    keys: dict[str, KeyCondIn] = {}       # 컬럼 → 키 조건


class GroupOut(BaseModel):
    key: str            # "_BS"|"_HT"|"_MA"|"_SM"|"기타"
    sql: str
    tables: list[str]


class MigrateResponse(BaseModel):
    sql: str
    generated: list[str]
    skipped: list[str]
    no_pk: list[str]
    groups: list[GroupOut]   # 접미사 그룹별 SQL(팝업 박스용)


class ExcludedTablesIn(BaseModel):
    tables: list[str]   # 설정 팝업의 전체 목록(추가/삭제 반영된 최종 상태) — 전체 교체로 저장


class ExcludedTablesOut(BaseModel):
    tables: list[str]   # 정렬된 대문자 예외 테이블명 목록


class ExcludedRefsIn(BaseModel):
    ids: list[str]   # 설정 팝업의 전체 목록(추가/삭제 반영된 최종 상태) — 전체 교체로 저장


class ExcludedRefsOut(BaseModel):
    ids: list[str]   # 정렬된 예외 ID 목록(대소문자 원형 보존 — 재귀 매칭이 대소문자 구분)


# DBIO는 resource_group이 파일 경로에 쓰이지 않아 2세그먼트(생략) 경로를 허용한다.
# Service/Batch/Biz는 resource_group이 필요하므로 3세그먼트 경로로 받는다(둘 다 같은 핸들러).
# 단건 조회 라우트 — extract-batch 도입(여러 ID 동시 추출) 이후 프론트는 이 라우트를 더 이상 호출하지 않는다. API·회귀 테스트 계약 유지 목적으로 남겨둠.
@router.get("/{module_type}/{file_id}", response_model=ExtractResponse)
@router.get("/{module_type}/{resource_group}/{file_id}", response_model=ExtractResponse)
def extract(
    module_type: Module_Type,
    file_id: str,
    resource_group: Optional[ResourceGroup] = None,
    reader: SourceReader = Depends(default_reader),
) -> ExtractResponse:
    """module_type/(resource_group)/ID → 원격 소스 → 참조 테이블 추출(dbio는 리프, 나머지는 재귀).

    resource_group은 DBIO에서만 생략 가능(2세그먼트). Service/Batch/Biz는 최상위 진입 모듈의
    업무그룹을 알아야 경로를 조합할 수 있어 필수(3세그먼트) — 재귀 중 발견되는 참조는
    service.extract_from_module 내부에서 알아서 find로 찾는다.
    """
    ident = file_id.strip()
    logger.info("extract 요청 수신: module_type=%s resource_group=%s file_id=%s", module_type, resource_group, ident)

    if not ident:
        logger.warning("extract 거부: 빈 ID")
        raise HTTPException(status_code=400, detail="ID is empty")

    if module_type != "dbio" and resource_group is None:
        logger.warning("extract 거부: resource_group 누락 module_type=%s", module_type)
        raise HTTPException(status_code=400, detail=f"resource_group required for {module_type}")

    try:
        result = service.extract(module_type, resource_group, ident, reader)
    except UnknownSqlType as e:
        logger.warning("extract 거부(ID 패턴 인식 불가): %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except SourceNotFound as e:
        logger.warning("extract 실패(파일 없음): %s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except SourceError as e:
        logger.warning("extract 실패(원격 접속): %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except ExtractionError as e:
        logger.warning("extract 실패(파싱): %s", e)
        raise HTTPException(status_code=400, detail=str(e))

    logger.info(
        "extract 완료: 테이블 %d개, DBIO %d개, batch 참조 %d개, service %d개, biz %d개",
        len(result.tables), len(result.dbios), len(result.batches), len(result.services), len(result.bizs),
    )
    return ExtractResponse(
        tables=result.tables, sql=result.sql, dbios=result.dbios, batches=result.batches,
        services=result.services, bizs=result.bizs,
    )


@router.post("/{module_type}/extract-batch", response_model=BatchExtractResponse)
def extract_batch(
    module_type: Module_Type,
    req: BatchExtractRequest,
    reader: SourceReader = Depends(default_reader),
) -> BatchExtractResponse:
    """module_type(+resource_group) + 여러 file_id → 병합된 결과 + 항목별 성공/실패.

    개별 항목의 404/503/400급 실패는 HTTP 에러로 올리지 않고 failed 배열에 담아 200으로
    반환한다(부분성공 허용). 요청 형태 자체가 잘못된 경우만(빈 목록/상한 초과/resource_group
    누락) 400으로 거부한다. 경로가 "batch"라는 단어를 쓰지만 module_type == "batch"(ProFrame
    배치 모듈)와는 무관 — extract-batch라는 라우트명으로 어휘 충돌을 피한다.
    """
    ids = [f.strip() for f in req.file_ids if f.strip()]
    logger.info("extract_batch 요청 수신: module_type=%s resource_group=%s file_ids=%d개",
                module_type, req.resource_group, len(req.file_ids))

    if not ids:
        logger.warning("extract_batch 거부: 유효한 ID 없음")
        raise HTTPException(status_code=400, detail="file_ids is empty")
    if len(ids) > MAX_BATCH_FILE_IDS:
        logger.warning("extract_batch 거부: ID %d개(상한 %d개 초과)", len(ids), MAX_BATCH_FILE_IDS)
        raise HTTPException(status_code=400, detail=f"file_ids exceeds max batch size ({MAX_BATCH_FILE_IDS})")
    if module_type != "dbio" and req.resource_group is None:
        logger.warning("extract_batch 거부: resource_group 누락 module_type=%s", module_type)
        raise HTTPException(status_code=400, detail=f"resource_group required for {module_type}")

    result = service.extract_batch(module_type, req.resource_group, req.file_ids, reader)

    def _status_for(e: Exception) -> int:
        if isinstance(e, (UnknownSqlType, ExtractionError)):
            return 400
        if isinstance(e, SourceNotFound):
            return 404
        if isinstance(e, SourceError):
            return 503
        return 500  # 방어적 폴백(service.extract_batch가 잡는 예외 종류상 도달하지 않음)

    logger.info("extract_batch 완료: 성공 %d개, 실패 %d개, 테이블 %d개",
                len(result.succeeded), len(result.failed), len(result.tables))
    return BatchExtractResponse(
        tables=result.tables, sql=result.sql, dbios=result.dbios, batches=result.batches,
        services=result.services, bizs=result.bizs, succeeded=result.succeeded,
        failed=[
            BatchFailedItem(file_id=f.file_id, error=f"{_status_for(f.error)}: {f.error}")
            for f in result.failed
        ],
    )


@router.post("/pks", response_model=PkResponse)
def pk_columns(req: PkRequest, db: DbClient = Depends(default_db)) -> PkResponse:
    """추출된 테이블 목록 → 테이블별 PK 컬럼(all_tables 딕셔너리 조회). 부작용 없는 조회."""
    logger.info("pks 요청 수신: 테이블 %d개", len(req.tables))
    try:
        pks = db_schema.fetch_pk_columns(req.tables, db)
    except DbError as e:
        logger.warning("pks 실패(DB 접속): %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except QueryError as e:
        logger.error("pks 실패(쿼리 실행): %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    logger.info("pks 완료: %d개 테이블 응답", len(pks))
    return PkResponse(pks=pks)


@router.post("/migrate-sql", response_model=MigrateResponse)
def migrate_sql(req: MigrateRequest, db: DbClient = Depends(default_db)) -> MigrateResponse:
    """대상 테이블 + 키 값 → 테이블별 DELETE/INSERT 생성. 오케스트레이션은 service에 위임."""
    logger.info("migrate-sql 요청 수신: 테이블 %d개, from=%s to=%s",
                len(req.tables), req.from_link or "-", req.to_link or "-")

    # HTTP 요청 모델(KeyCondIn) → 도메인 타입(migrate.KeyCond) 변환
    keys = {
        col: migrate.KeyCond(op=k.op, value=k.value, start=k.start, end=k.end)
        for col, k in req.keys.items()
    }

    try:
        result = service.migrate_sql(req.tables, keys, req.from_link, req.to_link, db)
    except DbError as e:
        logger.warning("migrate-sql 실패(DB 접속): %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except QueryError as e:
        logger.error("migrate-sql 실패(쿼리 실행): %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    logger.info("migrate-sql 완료: 생성 %d개, 제외 %d개",
                len(result.generated), len(result.skipped) + len(result.no_pk))
    return MigrateResponse(
        sql=result.sql,
        generated=result.generated,
        skipped=result.skipped,
        no_pk=result.no_pk,
        groups=[
            GroupOut(key=g.key, sql=g.sql, tables=g.tables) for g in result.groups
        ],
    )


@router.get("/excluded-tables", response_model=ExcludedTablesOut)
def get_excluded_tables() -> ExcludedTablesOut:
    """설정 팝업 진입 시 현재 저장된 예외 테이블 목록 조회."""
    return ExcludedTablesOut(tables=sorted(load_excluded_tables()))


@router.post("/excluded-tables", response_model=ExcludedTablesOut)
def put_excluded_tables(req: ExcludedTablesIn) -> ExcludedTablesOut:
    """설정 팝업의 저장 버튼 → 예외 테이블 목록 전체 교체 저장."""
    saved = save_excluded_tables(req.tables)
    logger.info("excluded-tables 저장 완료: %d개", len(saved))
    return ExcludedTablesOut(tables=sorted(saved))


@router.get("/excluded-refs", response_model=ExcludedRefsOut)
def get_excluded_refs() -> ExcludedRefsOut:
    """설정 팝업 진입 시 현재 저장된 재귀 참조 제외 ID 목록 조회."""
    return ExcludedRefsOut(ids=sorted(load_excluded_refs()))


@router.post("/excluded-refs", response_model=ExcludedRefsOut)
def put_excluded_refs(req: ExcludedRefsIn) -> ExcludedRefsOut:
    """설정 팝업의 저장 버튼 → 재귀 참조 제외 ID 목록 전체 교체 저장."""
    saved = save_excluded_refs(req.ids)
    logger.info("excluded-refs 저장 완료: %d개", len(saved))
    return ExcludedRefsOut(ids=sorted(saved))
