from __future__ import annotations


def strip_comments(text: str) -> tuple[str, int]:
    """C 소스에서 `//` 줄 주석과 `/* */` 블록 주석을 제거한다.

    문자열 리터럴(`"..."`)·문자 리터럴(`'...'`) 내부의 `//` `/*` 는 보존한다
    (오탐 방지). C 이스케이프(`\\"`, `\\\\` 등)를 인식해 리터럴 종료를
    정확히 판단하므로 `"a\\"//b"` 같은 문자열도 안전하다.

    주석 본문은 지우되 개행은 보존해 원본 줄 번호를 유지한다(향후 오류
    위치 추적 대비).

    반환: (정제된 텍스트, 제거된 주석 개수)
    """
    out: list[str] = []
    removed = 0
    i, n = 0, len(text)
    state = "normal"  # normal | squote | dquote | line_comment | block_comment

    while i < n:
        ch = text[i]

        if state == "normal":
            if ch == "/" and text[i + 1 : i + 2] == "/":
                state = "line_comment"
                removed += 1
                i += 2
                continue
            elif ch == "/" and text[i + 1 : i + 2] == "*":
                state = "block_comment"
                removed += 1
                i += 2
                continue
            elif ch == '"':
                state = "dquote"
                out.append(ch)
            elif ch == "'":
                state = "squote"
                out.append(ch)
            else:
                out.append(ch)
        elif state in ("squote", "dquote"):
            quote = '"' if state == "dquote" else "'"
            if ch == "\\" and i + 1 < n:
                out.append(ch)
                out.append(text[i + 1])
                i += 2
                continue
            out.append(ch)
            if ch == quote:
                state = "normal"
        elif state == "line_comment":
            if ch == "\n":
                out.append(ch)
                state = "normal"
        elif state == "block_comment":
            if ch == "\n":
                out.append(ch)
            elif ch == "*" and text[i + 1 : i + 2] == "/":
                state = "normal"
                i += 2
                continue

        i += 1

    return "".join(out), removed
