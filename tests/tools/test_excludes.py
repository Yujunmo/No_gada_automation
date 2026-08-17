"""load_excluded_refs 단위 테스트 (설정 파일 파싱)."""
from __future__ import annotations

from app.tools.table_extractor.excludes import load_excluded_refs


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
