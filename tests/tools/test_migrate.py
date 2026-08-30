"""
app/tools/data_migration/migrate.py 단위 테스트 (순수 함수, DB 무관).

DELETE/INSERT 생성 규칙을 고정: 자기 PK만 사용 / 값 이스케이프 / eq·between /
미입력 컬럼 조건 제외 / 전부 미입력 시 테이블 제외 / PK없음 제외 / dblink 부착.
"""
from __future__ import annotations

from app.tools.data_migration.migrate import KeyCond, build_migration_sql

PK = {
    "PFO_STCK_MA": ["mncm_code", "fund_code", "proc_date", "itms_code"],
    "PFO_SPA_ITMS_HT": ["proc_date", "itms_code"],
    "TRU_MNCM_BS": ["mncm_code"],
}


def test_full_conditions_with_from_and_to_links():
    keys = {
        "mncm_code": KeyCond(op="eq", value="M1"),
        "fund_code": KeyCond(op="eq", value="F1"),
        "itms_code": KeyCond(op="eq", value="I1"),
        "proc_date": KeyCond(op="between", start="20250101", end="20250131"),
    }
    r = build_migration_sql(["PFO_STCK_MA"], PK, keys, from_link="SRC", to_link="TGT")
    assert r.generated == ["PFO_STCK_MA"]
    # TO 링크 = DELETE/INSERT 대상, FROM 링크 = SELECT 소스
    assert "DELETE FROM PFO_STCK_MA@TGT" in r.sql
    assert "INSERT INTO PFO_STCK_MA@TGT" in r.sql
    assert "SELECT * FROM PFO_STCK_MA@SRC" in r.sql
    assert "proc_date BETWEEN '20250101' AND '20250131'" in r.sql
    # DELETE와 INSERT가 동일 WHERE를 공유
    assert r.sql.count("WHERE mncm_code = 'M1'") == 2


def test_each_table_uses_only_its_own_pk():
    keys = {
        "mncm_code": KeyCond(value="M1"),
        "fund_code": KeyCond(value="F1"),
        "itms_code": KeyCond(value="I1"),
        "proc_date": KeyCond(op="between", start="20250101", end="20250131"),
    }
    r = build_migration_sql(["PFO_SPA_ITMS_HT"], PK, keys)
    # proc_date, itms_code만 (mncm/fund 없음)
    assert "proc_date BETWEEN" in r.sql
    assert "itms_code = 'I1'" in r.sql
    assert "mncm_code" not in r.sql
    assert "fund_code" not in r.sql


def test_missing_value_column_omitted_but_table_generated():
    keys = {
        "mncm_code": KeyCond(value="M1"),
        "fund_code": KeyCond(value=""),          # 미입력 → 제외
        "itms_code": KeyCond(value=""),          # 미입력 → 제외
        "proc_date": KeyCond(op="eq", value="20250101"),
    }
    r = build_migration_sql(["PFO_STCK_MA"], PK, keys)
    assert r.generated == ["PFO_STCK_MA"]
    assert "mncm_code = 'M1'" in r.sql
    assert "proc_date = '20250101'" in r.sql
    assert "(미입력 조건 제외: fund_code, itms_code)" in r.sql
    # 제외된 컬럼은 조건절(=)에는 나오지 않음
    assert "fund_code = " not in r.sql
    assert "itms_code = " not in r.sql


def test_all_empty_table_skipped_to_avoid_full_delete():
    keys = {"mncm_code": KeyCond(value="")}
    r = build_migration_sql(["TRU_MNCM_BS"], PK, keys)
    assert r.generated == []
    assert r.skipped == ["TRU_MNCM_BS"]
    assert "전체 삭제 방지" in r.sql
    assert "DELETE FROM TRU_MNCM_BS" not in r.sql


def test_no_pk_table_excluded():
    r = build_migration_sql(["UNKNOWN_TBL"], {"UNKNOWN_TBL": []}, {})
    assert r.no_pk == ["UNKNOWN_TBL"]
    assert "PK 정보 없어 제외" in r.sql


def test_without_links_no_at_sign():
    keys = {"mncm_code": KeyCond(value="M1")}
    r = build_migration_sql(["TRU_MNCM_BS"], PK, keys)
    assert "DELETE FROM TRU_MNCM_BS\n" in r.sql
    assert "SELECT * FROM TRU_MNCM_BS\n" in r.sql
    assert "@" not in r.sql


def test_only_from_link_target_is_local():
    keys = {"mncm_code": KeyCond(value="M1")}
    r = build_migration_sql(["TRU_MNCM_BS"], PK, keys, from_link="SRC", to_link="")
    assert "DELETE FROM TRU_MNCM_BS\n" in r.sql        # TO 비움 → 로컬(링크 없음)
    assert "INSERT INTO TRU_MNCM_BS\n" in r.sql
    assert "SELECT * FROM TRU_MNCM_BS@SRC" in r.sql


def test_link_leading_at_is_stripped():
    keys = {"mncm_code": KeyCond(value="M1")}
    r = build_migration_sql(["TRU_MNCM_BS"], PK, keys, from_link="@SRC", to_link="@TGT")
    assert "FROM TRU_MNCM_BS@SRC" in r.sql
    assert "INTO TRU_MNCM_BS@TGT" in r.sql
    assert "@@" not in r.sql


def test_single_quote_escaped():
    keys = {"mncm_code": KeyCond(value="O'BRIEN")}
    r = build_migration_sql(["TRU_MNCM_BS"], PK, keys)
    assert "mncm_code = 'O''BRIEN'" in r.sql


# ---- 일반 PK 값에 쉼표로 여러 개를 주면 IN(...) ----

def test_comma_separated_value_becomes_in_clause():
    keys = {"mncm_code": KeyCond(value="M1,M2,M3")}
    r = build_migration_sql(["TRU_MNCM_BS"], PK, keys)
    assert "mncm_code IN ('M1', 'M2', 'M3')" in r.sql
    assert "mncm_code = " not in r.sql


def test_comma_separated_value_trims_whitespace_around_each_piece():
    keys = {"mncm_code": KeyCond(value=" M1 , M2 ,M3")}
    r = build_migration_sql(["TRU_MNCM_BS"], PK, keys)
    assert "mncm_code IN ('M1', 'M2', 'M3')" in r.sql


def test_comma_separated_value_drops_empty_pieces():
    keys = {"mncm_code": KeyCond(value="M1,,M2,")}
    r = build_migration_sql(["TRU_MNCM_BS"], PK, keys)
    assert "mncm_code IN ('M1', 'M2')" in r.sql


def test_single_value_with_trailing_comma_only_stays_eq():
    # 쉼표는 있지만 조각이 하나만 남으면 IN이 아니라 = 그대로.
    keys = {"mncm_code": KeyCond(value="M1,")}
    r = build_migration_sql(["TRU_MNCM_BS"], PK, keys)
    assert "mncm_code = 'M1'" in r.sql
    assert "IN (" not in r.sql


def test_comma_only_value_treated_as_empty_and_omitted():
    keys = {"mncm_code": KeyCond(value=",  ,")}
    r = build_migration_sql(["TRU_MNCM_BS"], PK, keys)
    assert r.skipped == ["TRU_MNCM_BS"]  # 유일한 PK 키가 결국 빈 값이라 전체삭제 방지로 제외


def test_comma_separated_value_escapes_quotes_per_piece():
    keys = {"mncm_code": KeyCond(value="O'BRIEN,M2")}
    r = build_migration_sql(["TRU_MNCM_BS"], PK, keys)
    assert "mncm_code IN ('O''BRIEN', 'M2')" in r.sql


def test_no_comma_single_value_unaffected():
    # 쉼표 없는 단일 값은 기존과 완전히 동일(trim 없이 그대로) — 회귀 방지.
    keys = {"mncm_code": KeyCond(value="  M1  ")}
    r = build_migration_sql(["TRU_MNCM_BS"], PK, keys)
    assert "mncm_code = '  M1  '" in r.sql


# ---- 접미사 그룹핑 ----

GPK = {
    "PFO_STCK_MA": ["mncm_code"],
    "PFO_FUND_BS": ["mncm_code"],
    "PFO_FUND_HT": ["mncm_code"],
    "PFO_TAMI_SM": ["mncm_code"],
    "PFO_STCK_TR": ["mncm_code"],   # _TR (기타와 독립)
    "SOME_ETC_XX": ["mncm_code"],   # 어느 접미사도 아님 → 기타
}
GKEYS = {"mncm_code": KeyCond(value="M1")}


def test_groups_by_suffix_in_fixed_order():
    tables = ["SOME_ETC_XX", "PFO_STCK_TR", "PFO_TAMI_SM", "PFO_STCK_MA", "PFO_FUND_HT", "PFO_FUND_BS"]
    r = build_migration_sql(tables, GPK, GKEYS)
    # 입력 순서와 무관하게 _BS, _HT, _MA, _SM, _TR, 기타 순
    assert [g.key for g in r.groups] == ["_BS", "_HT", "_MA", "_SM", "_TR", "기타"]


def test_group_contains_its_tables_and_sql():
    r = build_migration_sql(["PFO_STCK_MA", "PFO_STCK_TR"], GPK, GKEYS)
    by = {g.key: g for g in r.groups}
    assert by["_MA"].tables == ["PFO_STCK_MA"]
    assert "DELETE FROM PFO_STCK_MA" in by["_MA"].sql
    # _TR은 기타와 독립된 자기 그룹
    assert by["_TR"].tables == ["PFO_STCK_TR"]
    assert "DELETE FROM PFO_STCK_TR" in by["_TR"].sql
    assert "기타" not in by


def test_empty_groups_omitted():
    r = build_migration_sql(["PFO_FUND_BS"], GPK, GKEYS)
    assert [g.key for g in r.groups] == ["_BS"]


def test_excluded_tables_do_not_appear_in_groups():
    # PK 없는 테이블은 그룹에 안 들어감
    r = build_migration_sql(["UNKNOWN_MA"], {"UNKNOWN_MA": []}, GKEYS)
    assert r.groups == []
    assert r.no_pk == ["UNKNOWN_MA"]
