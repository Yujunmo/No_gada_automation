from __future__ import annotations

from app.common.text import sanitize_text


def test_zero_width_space_removed() -> None:
    # U+200B (제로폭공백)이 제거되고, 무엇을 지웠는지 리스트로 보고한다
    cleaned, removed = sanitize_text("A​B")
    assert cleaned == "AB"
    assert removed == ["U+200B"]


def test_various_format_chars_removed() -> None:
    # BOM(U+FEFF), 소프트하이픈(U+00AD), 방향마크(U+200E) 모두 Cf → 제거
    cleaned, removed = sanitize_text("﻿E­M‎P")
    assert cleaned == "EMP"
    assert removed == ["U+FEFF", "U+00AD", "U+200E"]


def test_unicode_spaces_normalized_to_ascii_space() -> None:
    # NBSP(U+00A0), 전각공백(U+3000) → 일반 공백으로 치환
    cleaned, removed = sanitize_text("FROM 　EMP")
    assert cleaned == "FROM  EMP"
    assert removed == ["U+00A0", "U+3000"]


def test_tabs_and_newlines_preserved() -> None:
    # 탭/개행(Cc)과 일반 공백은 손대지 않는다
    text = "SELECT *\n\tFROM EMP"
    cleaned, removed = sanitize_text(text)
    assert cleaned == text
    assert removed == []


def test_clean_text_unchanged() -> None:
    cleaned, removed = sanitize_text("SELECT * FROM EMP")
    assert cleaned == "SELECT * FROM EMP"
    assert removed == []
