from __future__ import annotations

from app.common.parse.sql import strip_db_links


def test_removes_dblink_no_space() -> None:
    cleaned, removed = strip_db_links("SELECT * FROM emp@remote")
    assert cleaned == "SELECT * FROM emp"
    assert removed == ["remote"]


def test_removes_dblink_with_space_before_at() -> None:
    # 실제 현장 케이스: 테이블명과 @ 사이 공백 (sqlglot이 파싱 실패하던 지점)
    cleaned, removed = strip_db_links("FROM pfo_fund_bs @dl_patru_Trups t1")
    assert cleaned == "FROM pfo_fund_bs t1"
    assert removed == ["dl_patru_Trups"]


def test_removes_multiple_dblinks_varied_spacing() -> None:
    cleaned, removed = strip_db_links("from a@l1 x, b @l2 y, c@ l3 z")
    assert cleaned == "from a x, b y, c z"
    assert removed == ["l1", "l2", "l3"]


def test_dblink_with_domain_name() -> None:
    cleaned, removed = strip_db_links("FROM emp@remote.world")
    assert cleaned == "FROM emp"
    assert removed == ["remote.world"]


def test_at_in_single_quote_string_preserved() -> None:
    sql = "SELECT * FROM emp WHERE email = 'hong@company.com'"
    cleaned, removed = strip_db_links(sql)
    assert cleaned == sql
    assert removed == []


def test_at_in_line_comment_preserved() -> None:
    sql = "SELECT * FROM emp -- ping a@b\n JOIN dept@lnk d"
    cleaned, removed = strip_db_links(sql)
    assert cleaned == "SELECT * FROM emp -- ping a@b\n JOIN dept d"
    assert removed == ["lnk"]


def test_at_in_block_comment_preserved() -> None:
    sql = "SELECT /* a@b */ * FROM emp@lnk"
    cleaned, removed = strip_db_links(sql)
    assert cleaned == "SELECT /* a@b */ * FROM emp"
    assert removed == ["lnk"]


def test_no_dblink_unchanged() -> None:
    sql = "SELECT * FROM emp JOIN dept ON emp.id = dept.id"
    cleaned, removed = strip_db_links(sql)
    assert cleaned == sql
    assert removed == []
