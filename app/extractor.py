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
        print(len(statements))

    except sqlglot.errors.ParseError as e:
        raise ExtractionError(_format_parse_error(e)) from e

    non_empty_trees = [s for s in statements if s is not None]
    if len(non_empty_trees) == 0:
        raise ExtractionError("No valid SQL statement found")
    
    tables: set[str] = set()
    for sql_tree in non_empty_trees:

        if not isinstance(sql_tree, VALID_TOP_LEVEL):
            raise ExtractionError(
                f"Unsupported or invalid SQL statement (got {type(sql_tree).__name__})"
            )

        cte_names = {
            (cte.alias or "").upper()
            for cte in sql_tree.find_all(exp.CTE)
            if cte.alias
        }

        for selects in sql_tree.args.get('selects', []):
            print(">> selects:" ,selects)
        

        for t in sql_tree.find_all(exp.Table):

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
