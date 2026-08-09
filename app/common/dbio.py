"""DBIO 원격 리소스 위치 규칙 + 조회.

ID 끝의 2글자 코드(예: DS200의 "DS")가 SQLTYPE 디렉토리를 확정하므로, 후보 디렉토리를
순회할 필요 없이 경로를 1회에 조합해 읽는다. table_extractor가 먼저 쓰지만 "DBIO ID로
원격 XML 읽기"는 다른 툴(예: Migration Builder)에서도 필요할 범용 ProFrame 동작이라 공용에 둔다.
"""
from __future__ import annotations

import re

from app.common.proframe import Prog
from app.common.source import SourceReader

# DBIO 리소스 위치 규칙: publish_ecams/resource/<PROG>/<SQLTYPE>/<ID>/<ID>.xml 의
# <PROG> 앞부분(서버/버전 고정 경로).
DBIO_RESOURCE_ROOT = "/src/truap01dap1/proframe/proframe5.0/publish_ecams/resource"

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


def classify_sqltype(id: str) -> str:
    m = ID_SUFFIX_RE.search(id.upper())
    if not m or m.group(1) not in SQL_TYPE_BY_SUFFIX:
        raise UnknownSqlType(f"ID에서 SQLTYPE을 판별할 수 없음(DF001,DS002,VS003 등): {id}")
    return SQL_TYPE_BY_SUFFIX[m.group(1)]


def read_dbio_xml(prog: Prog, id: str, reader: SourceReader) -> str:
    """ID 접미사로 SQLTYPE을 확정한 뒤 <PROG>/<SQLTYPE>/<ID>/<ID>.xml 을 조회한다."""
    sqltype = classify_sqltype(id)
    path = f"{DBIO_RESOURCE_ROOT}/{prog}/{sqltype}/{id}/{id}.xml"
    return reader.read(path)
 