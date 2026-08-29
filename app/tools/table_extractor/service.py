from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.common.io.db import DbClient
from app.common.io.sftp import SourceError, SourceNotFound, SourceReader
from app.common.parse.sql import ExtractionError
from app.common.proframe import Module_Type, ResourceGroup
from app.common.proframe import db_schema
from app.common.proframe.dbio import UnknownSqlType, dbio_referenced_tables
from app.common.proframe.module_source import load_group_map, read_module_source
from app.common.proframe.refs import scan_module_refs
from app.tools.table_extractor import migrate
from app.tools.table_extractor.excludes import load_excluded_refs, load_excluded_tables

logger = logging.getLogger("no_gada.table_extractor")


@dataclass
class ExtractResult:
    tables: list[str]
    sql: str
    dbios: list[str]
    batches: list[str] = field(default_factory=list)  # 참조만 되고 소스는 들여다보지 않은 배치 ID
    services: list[str] = field(default_factory=list)  # 재귀 중 실제로 읽어들인 service 모듈 ID(진입 모듈 포함)
    bizs: list[str] = field(default_factory=list)       # 재귀 중 실제로 읽어들인 biz 모듈 ID(진입 모듈 포함)


@dataclass
class FailedItem:
    file_id: str
    error: Exception   # 원본 예외를 그대로 보존 — 상태코드 매핑은 라우터의 기존 except 체인이 담당


@dataclass
class BatchExtractResult:
    tables: list[str]
    sql: str
    dbios: list[str]
    batches: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    bizs: list[str] = field(default_factory=list)
    succeeded: list[str] = field(default_factory=list)  # 성공한 file_id(입력 순서)
    failed: list[FailedItem] = field(default_factory=list)


def extract(module_type: Module_Type, resource_group: Optional[ResourceGroup], file_id: str, reader: SourceReader) -> ExtractResult:
    """module_type/(resource_group)/ID → 원격 소스 → 참조 테이블 추출.

    dbio는 참조가 없는 리프라 extract_from_dbio로 바로 끝나고, service/batch/biz는
    참조를 재귀적으로 따라가는 extract_from_module로 위임한다. 반환 직전에
    excluded_tables.txt(설정 팝업에서 등록한, 이관이 항상 불필요한 테이블) 목록으로
    최종 tables만 걸러낸다 — dbios/services/bizs 등 추출근거 트레이스는 그대로 둔다.
    """
    if module_type == "dbio":
        result = extract_from_dbio(file_id, reader)
    else:
        result = extract_from_module(module_type, resource_group, file_id, reader)

    excluded = load_excluded_tables()
    if excluded:
        result.tables = [t for t in result.tables if t not in excluded]

    return result


def extract_batch(
    module_type: Module_Type,
    resource_group: Optional[ResourceGroup],
    file_ids: list[str],
    reader: SourceReader,
) -> BatchExtractResult:
    """여러 file_id를 순차로 extract() 호출 → 성공은 UNION 병합, 실패는 개별 기록(부분성공).

    각 ID는 extract()를 독립적으로(visited=None) 호출한다 — extract_from_module 재귀 내부의
    개별 참조 실패는 이미 skip+warn되어 여기까지 올라오지 않고, 최상위 자체의 실패(소스 없음/
    접속 실패/파싱 실패)만 이 함수가 개별로 catch한다. excluded_tables 필터는 extract() 내부에서
    항목별로 이미 적용되므로(filter(A)∪filter(B) == filter(A∪B)) 병합 후 재필터링하지 않는다.

    dbios는 항목 간에 중복될 수 있다(각 항목이 독립된 visited라 순환 차단이 항목 간에는 없음) —
    별도 seen 집합으로 최초 등장 순서를 보존하며 dedupe한다. tables/batches/services/bizs는
    extract_from_module이 이미 set으로 병합해 반환하므로 단순 union이면 충분하다.
    """
    seen_ids: set[str] = set()
    cleaned_ids: list[str] = []
    for raw in file_ids:
        fid = raw.strip()
        if not fid or fid in seen_ids:
            continue
        seen_ids.add(fid)
        cleaned_ids.append(fid)

    tables: set[str] = set()
    sqls: list[str] = []
    dbios: list[str] = []
    dbios_seen: set[str] = set()
    batches: set[str] = set()
    services: set[str] = set()
    bizs: set[str] = set()
    succeeded: list[str] = []
    failed: list[FailedItem] = []

    for fid in cleaned_ids:
        try:
            result = extract(module_type, resource_group, fid, reader)
        except (SourceNotFound, SourceError, UnknownSqlType, ExtractionError) as e:
            logger.warning("extract_batch: 항목 실패(skip) file_id=%s: %s", fid, e)
            failed.append(FailedItem(file_id=fid, error=e))
            continue

        succeeded.append(fid)
        tables.update(result.tables)
        if result.sql:
            sqls.append(result.sql)
        for d in result.dbios:
            if d not in dbios_seen:
                dbios_seen.add(d)
                dbios.append(d)
        batches.update(result.batches)
        services.update(result.services)
        bizs.update(result.bizs)

    return BatchExtractResult(
        tables=sorted(tables), sql=";\n".join(sqls), dbios=dbios,
        batches=sorted(batches), services=sorted(services), bizs=sorted(bizs),
        succeeded=succeeded, failed=failed,
    )


def extract_from_dbio(file_id: str, reader: SourceReader) -> ExtractResult:
    """DBIO 리프: XML 조회 → <sqlString> 추출 → 테이블 추출(공용 dbio_referenced_tables 위임)."""
    tables, sql = dbio_referenced_tables(file_id, reader)
    logger.debug("extract_from_dbio: 테이블 %d개 집계 file_id=%s", len(tables), file_id)
    return ExtractResult(tables=tables, sql=sql, dbios=[file_id])


def extract_from_module(
    module_type: Module_Type,
    resource_group: Optional[str],
    file_id: str,
    reader: SourceReader,
    visited: Optional[set[str]] = None,
    excluded: Optional[set[str]] = None,
    group_map: Optional[dict[tuple[str, str], str]] = None,
) -> ExtractResult:
    """service/batch/biz 모듈 → 참조를 재귀적으로 따라가 도달한 DBIO의 SQL/테이블을 합산.

    최초 호출(visited=None — 라우터가 지정한 최상위 진입 모듈)의 소스 조회 실패는 그대로
    전파해 라우터가 404/503으로 매핑한다. 재귀 호출(visited가 전달됨) 중 만나는 개별
    DBIO/모듈 실패는 skip+warn 후 부분성공으로 처리한다. visited(file_id 집합, 재귀 전체가
    공유)로 순환 참조를 차단한다 — 타입이 달라도 같은 ID는 한 번만 처리한다.

    excluded(설정 파일 기반 항상-제외 ID 집합)는 재귀 중 "만나는" 참조에만 적용된다 —
    최상위 진입 모듈(top_level) 자체는 이 목록과 무관하게 항상 처리한다. 최초 호출 시
    None이면 load_excluded_refs()로 1회 로드해 재귀 전체에 그대로 전달한다.

    group_map(ID→업무그룹 사전 매핑, 있으면 read_module_source의 find 폴백을 가속)도
    excluded와 동일하게 최초 호출 시 load_group_map()으로 1회 로드해 재귀 전체에 그대로
    전달한다 — 매핑에 없거나 틀려도 read_module_source가 순차 탐색으로 알아서 폴백하므로
    안전하다.
    """
    top_level = visited is None
    if visited is None:
        visited = set()
    if excluded is None:
        excluded = load_excluded_refs()
    if group_map is None:
        group_map = load_group_map()
    visited.add(file_id)

    try:
        text = read_module_source(module_type, file_id, reader, resource_group=resource_group, group_map=group_map)
    except (SourceNotFound, SourceError) as e:
        if top_level:
            raise
        logger.warning(
            "extract_from_module: 소스 조회 실패(skip) module_type=%s file_id=%s: %s",
            module_type, file_id, e,
        )
        return ExtractResult(tables=[], sql="", dbios=[])

    logger.debug(
        "extract_from_module: 소스 조회 완료 module_type=%s file_id=%s (%d chars)",
        module_type, file_id, len(text),
    )

    # 소스를 실제로 읽는 데 성공한 시점에만 자기 자신을 기록한다(dbio의 자기 self-inclusion과 동일 규칙) —
    # 실패해서 위에서 이미 return/raise한 경우는 여기 도달하지 않는다.
    services: set[str] = set()
    bizs: set[str] = set()
    if module_type == "service":
        services.add(file_id)
    elif module_type == "biz":
        bizs.add(file_id)

    refs = scan_module_refs(text)
    logger.debug("extract_from_module: 참조 %d개 발견 file_id=%s", len(refs), file_id)

    tables: set[str] = set()
    sqls: list[str] = []
    dbios: list[str] = []
    batches: set[str] = set()

    for ref_type, ref_id in refs:
        if ref_id in visited:
            continue

        if ref_id in excluded:
            visited.add(ref_id)
            logger.debug("extract_from_module: 제외 목록에 있어 skip ref_type=%s ref_id=%s", ref_type, ref_id)
            continue

        if ref_type == "batch":
            # 배치는 별도 배치 잡 호출이라 소스까지 들여다보지 않고 참조된 이름만 기록한다.
            visited.add(ref_id)
            batches.add(ref_id)
            logger.debug("extract_from_module: batch 참조 기록(재귀 안 함) file_id=%s", ref_id)
            continue

        if ref_type == "dbio":
            visited.add(ref_id)
            try:
                result = extract_from_dbio(ref_id, reader)
            except (SourceNotFound, SourceError, UnknownSqlType, ExtractionError) as e:
                logger.warning("extract_from_module: DBIO 조회 실패(skip) file_id=%s: %s", ref_id, e)
                continue
        else:
            # 재귀 중 발견된 참조는 업무그룹을 모르므로 resource_group=None → find.
            result = extract_from_module(
                ref_type, None, ref_id, reader, visited=visited, excluded=excluded, group_map=group_map
            )

        tables.update(result.tables)
        if result.sql:
            sqls.append(result.sql)
        dbios.extend(result.dbios)
        batches.update(result.batches)
        services.update(result.services)
        bizs.update(result.bizs)

    return ExtractResult(
        tables=sorted(tables), sql=";\n".join(sqls), dbios=dbios, batches=sorted(batches),
        services=sorted(services), bizs=sorted(bizs),
    )


def migrate_sql(
    tables: list[str],
    keys: dict[str, migrate.KeyCond],
    from_link: str,
    to_link: str,
    db: DbClient,
) -> migrate.MigrationResult:
    """대상 테이블 + 키 → PK 컬럼 조회 후 DELETE/INSERT 조립(오케스트레이션).

    테이블명은 대문자 정규화, PK 컬럼은 all_tables에서 조회(신뢰 출처), 실제 SQL 문자열은
    순수 함수 migrate.build_migration_sql이 만든다. DB 오류(DbError/QueryError)는 그대로 전파돼
    라우터가 HTTP 상태로 매핑한다.
    """
    norm = [t.strip().upper() for t in tables if t.strip()]
    pk_map = db_schema.fetch_pk_columns(norm, db)
    logger.debug("service.migrate_sql: 테이블 %d개, PK 조회 완료", len(norm))
    return migrate.build_migration_sql(norm, pk_map, keys, from_link=from_link, to_link=to_link)
