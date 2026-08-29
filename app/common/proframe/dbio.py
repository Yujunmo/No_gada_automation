"""DBIO 원격 리소스 위치 규칙 + 조회.

ID 끝의 2글자 코드(예: DS200의 "DS")가 SQLTYPE 디렉토리를 확정하므로, 후보 디렉토리를
순회할 필요 없이 경로를 1회에 조합해 읽는다. table_extractor가 먼저 쓰지만 "DBIO ID로
원격 XML 읽기"는 다른 툴(예: Migration Builder)에서도 필요할 범용 ProFrame 동작이라 공용에 둔다.
"""
from __future__ import annotations

import os
import re

from app.common.io.sftp import SourceReader
from app.common.io.ssh import CommandRunner, grep_files
from app.common.parse.sql import extract_tables
from app.common.proframe import dbio_sql
from app.common.proframe.types import PROFRAME_ROOT

# DBIO 리소스 위치 규칙: release/dbio/xml/pfmDbio<ID>.xml (평면 구조 — PROG/SQLTYPE 하위 없음).
DBIO_RESOURCE_ROOT = f"{PROFRAME_ROOT}/release/dbio/xml"
# 실물 파일명 접두사(실제 회사 서버 규칙) — ID 자체에는 붙지 않음, 파일명 조합/역산에만 사용.
DBIO_FILENAME_PREFIX = "pfmDbio"

# ID 접미사 2글자 → SQLTYPE 디렉토리명 매핑.
SQL_TYPE_BY_SUFFIX = {
    "DF": "DYNAMICSQL", "DS": "DYNAMICSQL", "DI": "DYNAMICSQL", "DU": "DYNAMICSQL", "DD": "DYNAMICSQL",
    "EI": "EXECSQL", "EU": "EXECSQL", "ED": "EXECSQL",
    "PI": "PERSIST", "PU": "PERSIST", "PD": "PERSIST", "PS": "PERSIST", "PF": "PERSIST",
    "VF": "VIEW", "VS": "VIEW",
}
# ID 끝의 "2글자 + 숫자" 접미사(예: DS200)를 뽑아내는 패턴.
ID_SUFFIX_RE = re.compile(r"([A-Z]{2})\d+$")


class UnknownSqlType(Exception):
    """ID 끝의 2글자 코드가 알려진 SQLTYPE 패턴과 매칭되지 않음."""


def classify_sqltype(file_id: str) -> str:
    m = ID_SUFFIX_RE.search(file_id.upper())
    if not m or m.group(1) not in SQL_TYPE_BY_SUFFIX:
        raise UnknownSqlType(f"ID에서 SQLTYPE을 판별할 수 없음(DF001,DS002,VS003 등): {file_id}")
    return SQL_TYPE_BY_SUFFIX[m.group(1)]


def read_dbio_xml(file_id: str, reader: SourceReader) -> str:
    """ID 접미사를 검증한 뒤 release/dbio/xml/pfmDbio<ID>.xml 을 조회한다(평면 구조).

    `classify_sqltype`로 접미사가 인식 가능한 DBIO ID인지 검증해(미인식 → UnknownSqlType)
    잘못된 ID를 파일 없음(404)보다 명확한 400으로 먼저 걸러낸다.
    """
    classify_sqltype(file_id)  # 접미사 검증 전용 — 반환 SQLTYPE은 경로에 사용하지 않음.
    path = f"{DBIO_RESOURCE_ROOT}/{DBIO_FILENAME_PREFIX}{file_id}.xml"
    return reader.read(path)


def dbio_referenced_tables(file_id: str, reader: SourceReader) -> tuple[list[str], str]:
    """DBIO ID → XML 조회 → SQL 추출 → 참조 테이블(정렬) + SQL 이어붙임.

    read_dbio_xml + dbio_sql.extract_sql + extract_tables를 조합한 공용 파이프라인.
    table_extractor의 정방향 추출(extract_from_dbio)과 impact_analysis의 역방향 확정
    파싱(grep 후보를 실제 파싱으로 검증) 둘 다 이 함수를 공용으로 쓴다.

    예외는 그대로 전파한다: SourceNotFound/SourceError(read_dbio_xml → reader.read),
    UnknownSqlType(read_dbio_xml의 접미사 검증), ExtractionError(extract_tables).
    """
    xml_text = read_dbio_xml(file_id, reader)
    sqls = dbio_sql.extract_sql(xml_text)
    tables: set[str] = set()
    for sql in sqls:
        tables.update(extract_tables(sql))
    return sorted(tables), ";\n".join(sqls)


def find_dbios_referencing(table: str, searcher: CommandRunner) -> list[str]:
    """테이블명을 포함하는 DBIO XML을 grep해 그 DBIO ID **후보** 목록을 돌려준다.

    Impact Analysis 1홉의 싼 후보 필터다 — release/dbio/xml 아래 수천 개 XML을 열지 않고
    원격 grep으로 몇 개로 좁힌다. 놓침 0이 중요하므로 **느슨하게**(부분 문자열 허용) 잡고,
    오탐(컬럼명·주석·부분일치)은 후속 파싱 확정 단계가 거른다 — 즉 이 함수의 결과는
    "확정된 참조"가 아니라 "검사해볼 후보"다.

    grep이 돌려준 파일 경로에서 파일명(pfmDbio<ID>.xml)을 떼어 ID로 환원한다(평면 구조라
    basename에서 접두사·확장자만 벗기면 곧 ID). 대소문자는 grep이 무시하므로(-i) 테이블명
    케이스는 상관없다.
    """
    hits = grep_files(searcher, table.strip(), DBIO_RESOURCE_ROOT)
    ids = {
        os.path.basename(path)[len(DBIO_FILENAME_PREFIX): -len(".xml")]
        for path in hits
        if os.path.basename(path).startswith(DBIO_FILENAME_PREFIX) and path.endswith(".xml")
    }
    return sorted(ids)
 