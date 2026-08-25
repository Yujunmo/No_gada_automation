"""load/save_excluded_refs / load/save_excluded_tables 단위 테스트 (설정 파일 읽기·쓰기)."""
from __future__ import annotations

from app.tools.table_extractor.excludes import (
    load_excluded_refs,
    load_excluded_tables,
    save_excluded_refs,
    save_excluded_tables,
)


# ---- load_excluded_refs / save_excluded_refs (재귀 참조 제외, 설정 팝업 "모듈 예외처리"가 읽고 씀) ----

def test_parses_ids_ignoring_comments_and_blank_lines(tmp_path):
    p = tmp_path / "excluded_refs.txt"
    p.write_text(
        "# 헤더 주석\n"
        "\n"
        "PFO_LEGACY_MA_DS999\n"
        "  MZCOM_DeadBiz  \n"
        "BRLGRPRP0001 # 인라인 주석\n"
        "\n",
        encoding="utf-8",
    )
    assert load_excluded_refs(str(p)) == {"PFO_LEGACY_MA_DS999", "MZCOM_DeadBiz", "BRLGRPRP0001"}


def test_missing_file_returns_empty_set(tmp_path):
    assert load_excluded_refs(str(tmp_path / "no_such_file.txt")) == set()


def test_default_path_missing_returns_empty_set(monkeypatch, tmp_path):
    monkeypatch.setenv("NOGADA_EXCLUDED_REFS_PATH", str(tmp_path / "absent.txt"))
    assert load_excluded_refs() == set()


def test_env_var_overrides_default_path(monkeypatch, tmp_path):
    p = tmp_path / "custom.txt"
    p.write_text("SOME_ID\n", encoding="utf-8")
    monkeypatch.setenv("NOGADA_EXCLUDED_REFS_PATH", str(p))
    assert load_excluded_refs() == {"SOME_ID"}


def test_save_excluded_refs_preserves_case(tmp_path):
    # 테이블명과 달리 ID는 대문자로 정규화하면 안 된다(재귀 매칭이 대소문자 구분).
    p = tmp_path / "excluded_refs.txt"
    saved = save_excluded_refs(["  MZCOM_DeadBiz  ", "PFO_LEGACY_MA_DS999", "PFO_LEGACY_MA_DS999"], str(p))
    assert saved == {"MZCOM_DeadBiz", "PFO_LEGACY_MA_DS999"}
    assert p.read_text("utf-8") == "MZCOM_DeadBiz\nPFO_LEGACY_MA_DS999\n"


def test_save_excluded_refs_then_load_round_trips(tmp_path):
    p = tmp_path / "excluded_refs.txt"
    save_excluded_refs(["FooId", "BarId"], str(p))
    assert load_excluded_refs(str(p)) == {"FooId", "BarId"}


def test_save_excluded_refs_empty_list_clears_file(tmp_path):
    p = tmp_path / "excluded_refs.txt"
    save_excluded_refs(["FooId"], str(p))
    save_excluded_refs([], str(p))
    assert load_excluded_refs(str(p)) == set()


# ---- load_excluded_tables / save_excluded_tables (추출 결과 테이블 제외, 설정 팝업이 읽고 씀) ----

def test_parses_table_names_ignoring_comments_and_blank_lines(tmp_path):
    p = tmp_path / "excluded_tables.txt"
    p.write_text(
        "# 헤더 주석\n"
        "\n"
        "PFO_LEGACY_MA\n"
        "  tru_dead_ht  \n"
        "PFO_STCK_TR # 인라인 주석\n"
        "\n",
        encoding="utf-8",
    )
    # 대문자로 정규화되어 로드된다(테이블명 대문자 규약).
    assert load_excluded_tables(str(p)) == {"PFO_LEGACY_MA", "TRU_DEAD_HT", "PFO_STCK_TR"}


def test_excluded_tables_missing_file_returns_empty_set(tmp_path):
    assert load_excluded_tables(str(tmp_path / "no_such_file.txt")) == set()


def test_excluded_tables_default_path_missing_returns_empty_set(monkeypatch, tmp_path):
    monkeypatch.setenv("NOGADA_EXCLUDED_TABLES_PATH", str(tmp_path / "absent.txt"))
    assert load_excluded_tables() == set()


def test_excluded_tables_env_var_overrides_default_path(monkeypatch, tmp_path):
    p = tmp_path / "custom.txt"
    p.write_text("SOME_TABLE\n", encoding="utf-8")
    monkeypatch.setenv("NOGADA_EXCLUDED_TABLES_PATH", str(p))
    assert load_excluded_tables() == {"SOME_TABLE"}


def test_save_writes_normalized_sorted_names(tmp_path):
    p = tmp_path / "excluded_tables.txt"
    saved = save_excluded_tables(["  pfo_b  ", "PFO_A", "pfo_a"], str(p))
    assert saved == {"PFO_A", "PFO_B"}
    assert p.read_text("utf-8") == "PFO_A\nPFO_B\n"


def test_save_then_load_round_trips(tmp_path):
    p = tmp_path / "excluded_tables.txt"
    save_excluded_tables(["FOO", "BAR"], str(p))
    assert load_excluded_tables(str(p)) == {"FOO", "BAR"}


def test_save_overwrites_previous_contents(tmp_path):
    p = tmp_path / "excluded_tables.txt"
    save_excluded_tables(["FOO"], str(p))
    save_excluded_tables(["BAR"], str(p))
    assert load_excluded_tables(str(p)) == {"BAR"}


def test_save_creates_missing_parent_dir(tmp_path):
    p = tmp_path / "nested" / "dir" / "excluded_tables.txt"
    save_excluded_tables(["FOO"], str(p))
    assert load_excluded_tables(str(p)) == {"FOO"}


def test_save_empty_list_clears_file(tmp_path):
    p = tmp_path / "excluded_tables.txt"
    save_excluded_tables(["FOO"], str(p))
    save_excluded_tables([], str(p))
    assert load_excluded_tables(str(p)) == set()


# ---- NOGADA_SOURCE_ENCODING: 로컬 설정 파일도 회사 반입 시 이 env를 따른다 ----
# (io/sftp.py·io/ssh.py의 원격 소스 디코딩과 같은 env — 회사 텍스트 편집기가 UTF-8이
#  아니어도 사람이 config/*.txt를 직접 열어보는 시나리오까지 커버한다.)

def test_load_excluded_refs_reads_configured_encoding(monkeypatch, tmp_path):
    p = tmp_path / "excluded_refs.txt"
    p.write_bytes("한글_레거시_ID\n".encode("cp949"))
    monkeypatch.setenv("NOGADA_SOURCE_ENCODING", "cp949")
    assert load_excluded_refs(str(p)) == {"한글_레거시_ID"}


def test_load_excluded_tables_reads_configured_encoding(monkeypatch, tmp_path):
    p = tmp_path / "excluded_tables.txt"
    p.write_bytes("한글_테이블\n".encode("cp949"))
    monkeypatch.setenv("NOGADA_SOURCE_ENCODING", "cp949")
    assert load_excluded_tables(str(p)) == {"한글_테이블"}


def test_save_excluded_tables_writes_configured_encoding(monkeypatch, tmp_path):
    p = tmp_path / "excluded_tables.txt"
    monkeypatch.setenv("NOGADA_SOURCE_ENCODING", "cp949")
    save_excluded_tables(["한글_테이블"], str(p))
    assert p.read_bytes() == "한글_테이블\n".encode("cp949")


def test_save_excluded_refs_writes_configured_encoding(monkeypatch, tmp_path):
    p = tmp_path / "excluded_refs.txt"
    monkeypatch.setenv("NOGADA_SOURCE_ENCODING", "cp949")
    save_excluded_refs(["한글_ID"], str(p))
    assert p.read_bytes() == "한글_ID\n".encode("cp949")
