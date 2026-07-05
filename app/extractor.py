from __future__ import annotations

import sqlglot
from sqlglot import exp

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


def extract_tables(sql: str) -> list[str]:
    if not sql or not sql.strip():
        raise ExtractionError("Empty SQL input")

    try:
        statements = sqlglot.parse(sql, dialect="oracle")
        print(statements)
    except sqlglot.errors.ParseError as e:
        raise ExtractionError(_format_parse_error(e)) from e

    non_empty = [s for s in statements if s is not None]
    if len(non_empty) == 0:
        raise ExtractionError("No valid SQL statement found")
    if len(non_empty) > 1:
        raise ExtractionError(
            f"Multiple statements not supported (found {len(non_empty)})"
        )
    tree = non_empty[0]

    if not isinstance(tree, VALID_TOP_LEVEL):
        raise ExtractionError(
            f"Unsupported or invalid SQL statement (got {type(tree).__name__})"
        )

    cte_names = {
        (cte.alias or "").upper()
        for cte in tree.find_all(exp.CTE)
        if cte.alias
    }

    tables: set[str] = set()
    for t in tree.find_all(exp.Table):
        name = (t.name or "").upper().split("@", 1)[0]
        if not name:
            continue
        if name in cte_names:
            continue
        if name in EXCLUDED_EXACT:
            continue
        if any(name.startswith(p) for p in EXCLUDED_PREFIXES):
            continue
        tables.add(name)

    return sorted(tables)


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
