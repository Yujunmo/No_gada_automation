"""ProFrame DBIO published XML → SQL 문자열 추출.

루트 태그는 DYNAMICSQL/EXECSQL 등 SQLTYPE마다 다르지만(<dynamicSqlQuery>, <execSqlQuery> ...),
SQL 본문은 항상 <sqlString> 엘리먼트의 텍스트에 있다. 네임스페이스 유무와 무관하게
로컬네임(마지막 '}' 뒤 부분)으로 매칭해 루트 태그·네임스페이스 차이를 흡수한다.
"""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET

logger = logging.getLogger("no_gada.table_extractor")

_SQL_STRING_BLOCK_RE = re.compile(r"<sqlString[^>]*>(.*?)</sqlString>", re.DOTALL)
_ENTITIES = {"&lt;": "<", "&gt;": ">", "&amp;": "&", "&quot;": '"', "&apos;": "'"}


def _local_name(tag: str) -> str:
    return tag.split("}")[-1]


def _unescape(text: str) -> str:
    for entity, char in _ENTITIES.items():
        text = text.replace(entity, char)
    return text


def extract_sql(xml_text: str) -> list[str]:
    """<sqlString> 엘리먼트 텍스트를 등장 순서대로 전부 수집한다."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning("dbio_sql: XML 파싱 실패, 정규식 폴백 사용: %s", e)
        return [_unescape(m.group(1)) for m in _SQL_STRING_BLOCK_RE.finditer(xml_text)]

    return [
        el.text
        for el in root.iter()
        if _local_name(el.tag) == "sqlString" and el.text
    ]
