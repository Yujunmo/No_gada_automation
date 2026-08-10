from __future__ import annotations

import logging
from dataclasses import dataclass

from app.common import schema
from app.common.db import DbClient
from app.common.dbio import read_dbio_xml
from app.common.proframe import Module_Type, ResourceGroup
from app.common.sql import extract_tables
from app.common.source import SourceReader
from app.tools.table_extractor import mapper, migrate

logger = logging.getLogger("no_gada.table_extractor")


@dataclass
class ExtractResult:
    tables: list[str]
    sql: str
    dbios: list[str]


def extract(module_type: Module_Type, resource_group: ResourceGroup, file_id: str, reader: SourceReader) -> ExtractResult:
    if module_type != "dbio":
        raise NotImplementedError(f"module_type={module_type} not yet supported")

    xml_text = read_dbio_xml(file_id, reader)
    logger.debug("service.extract: XML 조회 완료 resource_group=%s file_id=%s (%d chars)", resource_group, file_id, len(xml_text))

    sqls = mapper.extract_sql(xml_text)
    logger.debug("service.extract: SQL %d개 추출 file_id=%s", len(sqls), file_id)

    tables: set[str] = set()
    for sql in sqls:
        tables.update(extract_tables(sql))
    logger.debug("service.extract: 테이블 %d개 집계 file_id=%s", len(tables), file_id)

    return ExtractResult(tables=sorted(tables), sql=";\n".join(sqls), dbios=[file_id])


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
    pk_map = schema.fetch_pk_columns(norm, db)
    logger.debug("service.migrate_sql: 테이블 %d개, PK 조회 완료", len(norm))
    return migrate.build_migration_sql(norm, pk_map, keys, from_link=from_link, to_link=to_link)
