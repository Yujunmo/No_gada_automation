from __future__ import annotations

import logging

import sqlglot
from sqlglot import exp

from app.common.text import sanitize_text

logger = logging.getLogger("no_gada.sql_bench")

EXCLUDED_EXACT = {"DUAL"}
EXCLUDED_PREFIXES = ("USER_", "ALL_", "DBA_", "V$", "GV$", "SYS.")

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


# 파싱 #추출 #조합
def extract_tables(sql: str) -> list[str]:
    """Oracle SQL(단일/다중 문장)에서 참조하는 물리 테이블명을 정렬해 반환한다."""
    tables: set[str] = set()
    for tree in _parse_statements(sql): 
        tables |= _tables_in(tree) 
    return sorted(tables)


def _parse_statements(sql: str) -> list[exp.Expression]:
    """입력 정제 → Oracle 파싱 → 문장 검증. 유효한 최상위 문장 트리 목록을 반환한다."""
    if not sql or not sql.strip():
        raise ExtractionError("Empty SQL input")

    sql, removed = sanitize_text(sql)
    if removed:
        logger.warning(
            "보이지 않는 문자 %d개 제거/정규화: %s", len(removed), ", ".join(removed)
        )

    try:
        statements = sqlglot.parse(sql, dialect="oracle")
    except sqlglot.errors.ParseError as e:
        raise ExtractionError(_format_parse_error(e)) from e

    trees = [s for s in statements if s is not None]
    if not trees:
        raise ExtractionError("No valid SQL statement found")

    logger.debug(f"파싱 완료: {len(trees)}개 문장")
    for i, tree in enumerate(trees):
        logger.debug(f"tree {i}: {type(tree)}")
        if not isinstance(tree, VALID_TOP_LEVEL):
            raise ExtractionError(
                f"Unsupported or invalid SQL statement (got {type(tree).__name__})"
            )
    return trees


def _tables_in(tree: exp.Expression) -> set[str]:
    """한 문장 트리에서 제외 규칙(CTE alias / DUAL / 딕셔너리·동적 뷰)을 적용해
    물리 테이블명 집합을 뽑는다. DB 링크(@)·스키마 프리픽스는 제거된 상태로 반환."""
    cte_names = {
        (cte.alias or "").upper()
        for cte in tree.find_all(exp.CTE)
        if cte.alias
    }

    tables: set[str] = set()
    for t in tree.find_all(exp.Table):
        name = (t.name or "").upper().split("@", 1)[0].strip()
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
