"""
app/common/proframe/db_schema.py 단위 테스트.

네트워크 없이 인메모리 FakeDb로 fetch_pk_columns의 계약을 고정한다:
그룹핑 / 없는 테이블 [] / 대문자·중복 정규화 / 컬럼 순서 보존 / 단일 쿼리 / 빈 입력 무쿼리.
"""
from __future__ import annotations

from app.common.io.db import Params, Row
from app.common.proframe.db_schema import fetch_pk_columns


class FakeDb:
    """table_id/pk_column 행을 되돌려주는 가짜 DbClient. query 호출을 기록한다."""

    def __init__(self, rows: list[Row]):
        self._rows = rows
        self.calls: list[tuple[str, Params]] = []

    def query(self, sql: str, params: Params = None) -> list[Row]:
        self.calls.append((sql, params))
        # IN 절 매칭 흉내: params["tables"](대문자 테이블명 리스트)에 포함된 행만 반환
        wanted = set((params or {}).get("tables", []))
        return [r for r in self._rows if r["table_id"] in wanted]


ROWS = [
    {"table_id": "PFO_STCK_MA", "pk_column": "mncm_code"},
    {"table_id": "PFO_STCK_MA", "pk_column": "fund_code"},
    {"table_id": "PFO_STCK_MA", "pk_column": "proc_date"},
    {"table_id": "PFO_STCK_MA", "pk_column": "itms_code"},
    {"table_id": "PFO_FUND_BS", "pk_column": "mncm_code"},
    {"table_id": "PFO_FUND_BS", "pk_column": "fund_code"},
]


def test_groups_by_table_preserving_order():
    db = FakeDb(ROWS)
    out = fetch_pk_columns(["PFO_STCK_MA", "PFO_FUND_BS"], db)
    assert out == {
        "PFO_STCK_MA": ["mncm_code", "fund_code", "proc_date", "itms_code"],
        "PFO_FUND_BS": ["mncm_code", "fund_code"],
    }


def test_unknown_table_yields_empty_list():
    db = FakeDb(ROWS)
    out = fetch_pk_columns(["PFO_STCK_MA", "ZZZ"], db)
    assert out["PFO_STCK_MA"]  # 존재
    assert out["ZZZ"] == []    # 딕셔너리에 없어도 키는 포함


def test_normalizes_case_and_whitespace_and_dedups():
    db = FakeDb(ROWS)
    out = fetch_pk_columns([" pfo_stck_ma ", "PFO_STCK_MA", "pfo_fund_bs"], db)
    # 대문자·공백 정규화 후 중복 제거 → 2개 키
    assert set(out) == {"PFO_STCK_MA", "PFO_FUND_BS"}
    # 쿼리 1회, 파라미터는 정규화된 유니크 목록
    assert len(db.calls) == 1
    _, params = db.calls[0]
    assert params["tables"] == ["PFO_STCK_MA", "PFO_FUND_BS"]


def test_empty_input_does_not_query():
    db = FakeDb(ROWS)
    assert fetch_pk_columns([], db) == {}
    assert fetch_pk_columns(["   ", ""], db) == {}
    assert db.calls == []  # 빈 입력은 쿼리하지 않음


def test_single_query_uses_named_in_bind():
    db = FakeDb(ROWS)
    fetch_pk_columns(["PFO_STCK_MA", "PFO_FUND_BS"], db)
    sql, params = db.calls[0]
    assert "IN :tables" in sql
    assert params["tables"] == ["PFO_STCK_MA", "PFO_FUND_BS"]
