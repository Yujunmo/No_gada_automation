from __future__ import annotations

import logging
import re

import sqlglot
from sqlglot import exp

from app.common.parse.text_sanitize import sanitize_text

logger = logging.getLogger("no_gada.sql")

EXCLUDED_EXACT = {"DUAL"}
EXCLUDED_PREFIXES = ("USER_", "ALL_", "DBA_", "V$", "GV$", "SYS.")

# db link 이름: 식별자 문자 + 도메인 구분용 '.' (예: remote.world)
_DBLINK_NAME = re.compile(r"[A-Za-z0-9_$#.]+")

VALID_TOP_LEVEL = (
    exp.Select,
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Merge,
    exp.Union,
    exp.MultitableInserts,
)

class ExtractionError(Exception):
    pass


def strip_db_links(sql: str) -> tuple[str, list[str]]:
    """SQL 텍스트에서 `@dblink` 참조를 제거한다.

    `테이블@링크` / `테이블 @ 링크`(공백 허용, 실제 Oracle 문법)를 모두 잡아
    링크 부분과 `@` 앞 공백을 지운다. sqlglot이 `@` 앞 공백에서 파싱 실패하므로
    파싱 전처리로 쓰인다.

    **따옴표 문자열·주석(`--`, `/* */`) 내부의 `@`는 보존**한다(이메일 등 오탐 방지).
    반환: (정제된 SQL, 제거된 db link명 목록)
    """
    out: list[str] = []
    removed: list[str] = []
    i, n = 0, len(sql)
    state = "normal"  # normal | squote | dquote | line_comment | block_comment

    while i < n:
        ch = sql[i]

        if state == "normal":
            if ch == "-" and sql[i + 1 : i + 2] == "-":
                state = "line_comment"
                out.append(ch)
            elif ch == "/" and sql[i + 1 : i + 2] == "*":
                state = "block_comment"
                out.append(ch)
            elif ch == "'":
                state = "squote"
                out.append(ch)
            elif ch == '"':
                state = "dquote"
                out.append(ch)
            elif ch == "@":
                # @ 앞 공백까지 제거 (`emp @lnk` → `emp`)
                while out and out[-1] in " \t":
                    out.pop()
                i += 1
                while i < n and sql[i] in " \t\r\n":
                    i += 1
                m = _DBLINK_NAME.match(sql, i)
                if m:
                    removed.append(m.group(0))
                    i = m.end()
                continue  # i 이미 전진시킴
            else:
                out.append(ch)
        elif state == "squote":
            out.append(ch)
            if ch == "'":
                state = "normal"
        elif state == "dquote":
            out.append(ch)
            if ch == '"':
                state = "normal"
        elif state == "line_comment":
            out.append(ch)
            if ch == "\n":
                state = "normal"
        elif state == "block_comment":
            out.append(ch)
            if ch == "*" and sql[i + 1 : i + 2] == "/":
                out.append("/")
                i += 2
                state = "normal"
                continue

        i += 1

    return "".join(out), removed


# 파싱 #추출 #조합
def     extract_tables(sql: str) -> list[str]:
    """Oracle SQL(단일/다중 문장)에서 참조하는 물리 테이블명을 정렬해 반환한다."""
    tables: set[str] = set()
    for ast in _parse_asts(_preprocess(sql)):
        tables |= _tables_in(ast)
    return sorted(tables)


def _preprocess(sql: str) -> str:
    """원문 정제(텍스트 단계). 보이지 않는 문자 제거 + db link 스트립.

    AST와 무관한 순수 문자열 처리만 한다. 빈 입력은 여기서 방어한다.
    """
    if not sql or not sql.strip():
        raise ExtractionError("Empty SQL input")

    sql, removed = sanitize_text(sql)
    if removed:
        logger.warning(
            "보이지 않는 문자 %d개 제거/정규화: %s", len(removed), ", ".join(removed)
        )

    sql, links = strip_db_links(sql)
    if links:
        logger.debug("db link %d개 제거: %s", len(links), ", ".join(links))

    return sql


def _parse_asts(sql: str) -> list[exp.Expression]:
    """정제된 SQL → Oracle 파싱 → 최상위 문장 검증. 유효한 AST 목록을 반환한다."""
    try:
        statements = sqlglot.parse(sql, dialect="oracle")
    except sqlglot.errors.ParseError as e:
        raise ExtractionError(_format_parse_error(e)) from e

    asts = [s for s in statements if s is not None]
    if not asts:
        raise ExtractionError("No valid SQL statement found")

    logger.debug(f"파싱 완료: {len(asts)}개 문장")
    for i, ast in enumerate(asts):
        logger.debug(f"ast {i}: {type(ast)}")
        if not isinstance(ast, VALID_TOP_LEVEL):
            raise ExtractionError(
                f"Unsupported or invalid SQL statement (got {type(ast).__name__})"
            )
    return asts


def _tables_in(ast: exp.Expression) -> set[str]:
    """한 문장 AST에서 제외 규칙(CTE alias / DUAL / 딕셔너리·동적 뷰)을 적용해
    물리 테이블명 집합을 뽑는다. DB 링크(@)·스키마 프리픽스는 제거된 상태로 반환."""
    cte_names = {
        (cte.alias or "").upper()
        for cte in ast.find_all(exp.CTE)
        if cte.alias
    }

    tables: set[str] = set()
    for t in ast.find_all(exp.Table):
        # db link는 파싱 전 strip_db_links로 이미 제거됨
        name = (t.name or "").upper().strip()
        if not name or name in cte_names or name in EXCLUDED_EXACT:
            continue
        if any(name.startswith(p) for p in EXCLUDED_PREFIXES):
            continue
        tables.add(name)
    return tables


def _format_parse_error(e: sqlglot.errors.ParseError) -> str:
    errors = getattr(e, "errors", None)
    if not errors:
        return str(e)
    parts = []
    for err in errors:
        line = err.get("line")
        col = err.get("col")
        desc = err.get("description", "")
        loc = f"line {line}, col {col}" if line and col else ""
        parts.append(f"Parse error at {loc}: {desc}" if loc else f"Parse error: {desc}")
    return "; ".join(parts)
