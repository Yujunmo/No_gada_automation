"""DBIO 원격 리소스 위치 규칙 + 조회.

ID 끝의 2글자 코드(예: DS200의 "DS")가 SQLTYPE 디렉토리를 확정하므로, 후보 디렉토리를
순회할 필요 없이 경로를 1회에 조합해 읽는다. table_extractor가 먼저 쓰지만 "DBIO ID로
원격 XML 읽기"는 다른 툴(예: Migration Builder)에서도 필요할 범용 ProFrame 동작이라 공용에 둔다.
"""
from __future__ import annotations

import re

from app.common.io.sftp import SourceReader
from app.common.proframe.types import PROFRAME_ROOT

# DBIO 리소스 위치 규칙: release/dbio/xml/<ID>.xml (평면 구조 — PROG/SQLTYPE 하위 없음).
DBIO_RESOURCE_ROOT = f"{PROFRAME_ROOT}/release/dbio/xml"

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
    """ID 접미사를 검증한 뒤 release/dbio/xml/<ID>.xml 을 조회한다(평면 구조).

    `classify_sqltype`로 접미사가 인식 가능한 DBIO ID인지 검증해(미인식 → UnknownSqlType)
    잘못된 ID를 파일 없음(404)보다 명확한 400으로 먼저 걸러낸다.
    """
    classify_sqltype(file_id)  # 접미사 검증 전용 — 반환 SQLTYPE은 경로에 사용하지 않음.
    path = f"{DBIO_RESOURCE_ROOT}/{file_id}.xml"
    return reader.read(path)
 