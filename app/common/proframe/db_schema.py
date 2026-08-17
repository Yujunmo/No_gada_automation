"""테이블 딕셔너리 조회 (툴 공용 DB 도메인 로직).

`all_tables`(테이블명 → PK 컬럼명 매핑, 복합키는 테이블당 여러 행)를 조회해 "테이블별 PK 컬럼"을
돌려준다. DB I/O 자체는 `db.py`(`DbClient.query`)에 있고, 이 모듈은 그 위에 얹힌 딕셔너리 조회
도메인 로직이다(`dbio.read_dbio_xml`이 `io/sftp.py` 위에 얹힌 것과 동일 구조). table_extractor가
먼저 쓰지만 "테이블 → PK 컬럼"은 다른 툴(예: Migration Builder)에서도 필요할 범용 동작이라 공용에 둔다.
"""
from __future__ import annotations

import logging
from typing import Sequence

from app.common.io.db import DbClient

logger = logging.getLogger("no_gada.schema")

# PK 딕셔너리 테이블(nogada.all_tables). 회사 반입 시 실제 딕셔너리 뷰/테이블로 교체 지점.
ALL_TABLES = "all_tables"


def fetch_pk_columns(tables: Sequence[str], db: DbClient) -> dict[str, list[str]]:
    """테이블명 목록 → {테이블명: [PK 컬럼, ...]}.

    all_tables를 **1회 쿼리**로 조회해 테이블별로 그룹핑한다. 요청한 모든 테이블을 키로 포함하며,
    딕셔너리에 없는 테이블은 빈 리스트(`[]`)로 채운다(프론트의 "PK 정보 없음" 표시·교집합 계산용).
    컬럼 순서는 DB 행 순서를 보존한다(복합키 자연순서 유지).
    """
    # 정규화: 공백 제거 + 대문자화(all_tables.table_id는 대문자 저장) + 순서 유지 중복 제거.
    seen: dict[str, None] = {}
    for t in tables:
        norm = t.strip().upper()
        if norm:
            seen.setdefault(norm, None)
    names = list(seen)
    if not names:
        return {}

    placeholders = ", ".join(["%s"] * len(names))
    sql = f"SELECT table_id, pk_column FROM {ALL_TABLES} WHERE table_id IN ({placeholders})"
    rows = db.query(sql, names)

    result: dict[str, list[str]] = {name: [] for name in names}
    for row in rows:
        # table_id는 대문자 저장이지만 방어적으로 정규화해 요청 키에 맞춘다.
        key = str(row["table_id"]).strip().upper()
        if key in result:
            result[key].append(row["pk_column"])
    logger.debug("fetch_pk_columns: %d개 테이블 요청 → %d개 PK행", len(names), len(rows))
    return result
