from __future__ import annotations

from app.common.parse.c_source import strip_comments


def test_removes_line_comment() -> None:
    cleaned, removed = strip_comments("int a = 1; // comment\nint b = 2;")
    assert cleaned == "int a = 1; \nint b = 2;"
    assert removed == 1


def test_removes_block_comment_single_line() -> None:
    cleaned, removed = strip_comments("int a = /* skip */ 1;")
    assert cleaned == "int a =  1;"
    assert removed == 1


def test_removes_block_comment_multiline_preserves_newlines() -> None:
    src = "int a = /*\nline1\nline2\n*/ 1;"
    cleaned, removed = strip_comments(src)
    assert cleaned == "int a = \n\n\n 1;"
    assert removed == 1


def test_dead_code_in_line_comment_removed() -> None:
    # SPCSP53619C.c 실물 케이스: 주석 처리된 죽은 코드 안의 콜 매크로가
    # scan_module_refs 정규식에 오탐되지 않도록 주석째 제거돼야 한다.
    src = '// PFM_TRYNJ(pfmDbioCloseCursorArray("OK_IMSI_META_VF001"))\nint x = 1;'
    cleaned, removed = strip_comments(src)
    assert "pfmDbioCloseCursorArray" not in cleaned
    assert removed == 1


def test_slash_in_double_quote_string_preserved() -> None:
    src = 'char *s = "http://example.com";'
    cleaned, removed = strip_comments(src)
    assert cleaned == src
    assert removed == 0


def test_comment_marker_in_char_literal_preserved() -> None:
    src = "char c = '/';"
    cleaned, removed = strip_comments(src)
    assert cleaned == src
    assert removed == 0


def test_escaped_quote_in_string_does_not_end_literal_early() -> None:
    src = 'char *s = "a\\"//b"; // real comment\n'
    cleaned, removed = strip_comments(src)
    assert cleaned == 'char *s = "a\\"//b"; \n'
    assert removed == 1


def test_no_comment_unchanged() -> None:
    src = "PFM_TRYNJ(pfmDbioSelect(\"PFO_ABC_DS101\", &in, &out));"
    cleaned, removed = strip_comments(src)
    assert cleaned == src
    assert removed == 0
