from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from typing import Literal

from app.common import schema
from app.common.db import DbClient, DbError, QueryError, default_db
from app.common.dbio import UnknownSqlType
from app.common.proframe import Module_Type, ResourceGroup
from app.common.sql import ExtractionError
from app.common.source import SourceNotFound, SourceReader, default_reader
from app.tools.table_extractor import migrate, service

logger = logging.getLogger("no_gada.table_extractor")

router = APIRouter(prefix="/table-extractor")


class ExtractResponse(BaseModel):
    tables: list[str]  # 정렬된 대문자 물리 테이블명 합집합
    sql: str           # 수집한 SQL(우측 패널 표시용, ;로 연결)
    dbios: list[str]   # 해석 과정에서 도달한 DBIO ID 목록(참고용)


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


@router.get("/{module_type}/{resource_group}/{file_id}", response_model=ExtractResponse)
def extract(
    module_type: Module_Type,
    resource_group: ResourceGroup,
    file_id: str,
    reader: SourceReader = Depends(default_reader),
) -> ExtractResponse:
    """module_type/resource_group/ID → 원격 소스 → 참조 테이블 추출. 현재는 DBIO만 구현됨."""
    ident = file_id.strip()
    logger.info("extract 요청 수신: module_type=%s resource_group=%s file_id=%s", module_type, resource_group, ident)

    if not ident:
        logger.warning("extract 거부: 빈 ID")
        raise HTTPException(status_code=400, detail="ID is empty")

    if module_type != "dbio":
        logger.warning("extract 미구현: module_type=%s", module_type) # dbio 외의 module_type은 아직 구현되지 않음
        raise HTTPException(status_code=501, detail=f"module_type={module_type} not implemented yet")

    try:
        result = service.extract(module_type, resource_group, ident, reader)
    except UnknownSqlType as e:
        logger.warning("extract 거부(ID 패턴 인식 불가): %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except SourceNotFound as e:
        logger.warning("extract 실패(파일 없음): %s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except ExtractionError as e:
        logger.warning("extract 실패(파싱): %s", e)
        raise HTTPException(status_code=400, detail=str(e))

    logger.info("extract 완료: 테이블 %d개, DBIO %d개", len(result.tables), len(result.dbios))
    return ExtractResponse(tables=result.tables, sql=result.sql, dbios=result.dbios)


@router.post("/pks", response_model=PkResponse)
def pk_columns(req: PkRequest, db: DbClient = Depends(default_db)) -> PkResponse:
    """추출된 테이블 목록 → 테이블별 PK 컬럼(all_tables 딕셔너리 조회). 부작용 없는 조회."""
    logger.info("pks 요청 수신: 테이블 %d개", len(req.tables))
    try:
        pks = schema.fetch_pk_columns(req.tables, db)
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
