"""이관(DELETE/INSERT) SQL 생성 — 순수 로직(DB·HTTP 비의존, 테스트 가능).

입력: 대상 테이블 목록 + 테이블별 PK 컬럼(pk_map) + 컬럼별 키 조건(keys) + FROM/TO DB 링크.
출력: 대상 테이블마다 `DELETE FROM t@<TO> WHERE ...` + `INSERT INTO t@<TO> SELECT * FROM t@<FROM> WHERE ...`.
      FROM = 원격 소스(데이터를 읽어옴), TO = 대상(삭제 후 넣음). TO 비우면 로컬(링크 없음).

규칙(프론트에서 백엔드로 이관한 계약):
- 각 테이블은 **자기 PK 컬럼만**(pk_map[t]) 조건에 사용, AND 결합.
- 값은 전부 문자열 따옴표(작은따옴표는 '' 로 이스케이프). 날짜/문자 구분은 하지 않는다(UI 관심사).
- 조건 종류: eq → `col = 'v'`, between → `col BETWEEN 'a' AND 'b'`.
- **값이 빈 컬럼은 조건절에서 제외**(테이블은 계속 생성)하고 주석에 표기.
- 한 테이블의 키가 **전부 비면** WHERE가 없어 전체 삭제가 되므로 그 테이블은 안전상 제외.
- PK 정보가 없는(딕셔너리 미등록) 테이블도 제외. 링크 미입력이면 `@` 생략.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KeyCond:
    """컬럼 하나의 키 조건. op=eq면 value, op=between이면 start/end 사용."""
    op: str = "eq"          # "eq" | "between"
    value: str = ""
    start: str = ""
    end: str = ""


# 테이블 접미사 → 그룹. 이 순서로 노출하고, 어디에도 안 맞으면 "기타"(마지막).
GROUP_ORDER = ["_BS", "_HT", "_MA", "_SM", "_TR"]
GROUP_OTHER = "기타"


@dataclass
class MigrationGroup:
    key: str                                              # "_BS"|"_HT"|"_MA"|"_SM"|"기타"
    sql: str                                              # 그룹 내 블록들을 \n\n 로 이음
    tables: list[str] = field(default_factory=list)


@dataclass
class MigrationResult:
    sql: str
    generated: list[str] = field(default_factory=list)  # 실제 생성된 테이블
    skipped: list[str] = field(default_factory=list)     # 입력 키가 없어 제외(전체 삭제 방지)
    no_pk: list[str] = field(default_factory=list)        # PK 정보 없어 제외
    groups: list[MigrationGroup] = field(default_factory=list)  # 접미사 그룹별 SQL(팝업 표시용)


def _group_key(table: str) -> str:
    """테이블명 접미사로 그룹 키를 정한다."""
    up = table.upper()
    for suf in GROUP_ORDER:
        if up.endswith(suf):
            return suf
    return GROUP_OTHER


def _quote(v: str) -> str:
    """Oracle 문자열 리터럴 이스케이프(작은따옴표 → '')."""
    return v.replace("'", "''")


def _condition(col: str, kc: KeyCond) -> str | None:
    """컬럼 조건 하나를 만든다. 값이 없으면 None(조건절에서 제외)."""
    if kc.op == "between":
        if kc.start and kc.end:
            return f"{col} BETWEEN '{_quote(kc.start)}' AND '{_quote(kc.end)}'"
        return None
    if kc.value:
        return f"{col} = '{_quote(kc.value)}'"
    return None


def _at(link: str) -> str:
    """DB 링크 문자열 → `@링크`(비었으면 ''). 앞의 `@`는 중복 제거."""
    link = link.strip().lstrip("@")
    return f"@{link}" if link else ""


def build_migration_sql(
    tables: list[str],
    pk_map: dict[str, list[str]],
    keys: dict[str, KeyCond],
    from_link: str = "",
    to_link: str = "",
) -> MigrationResult:
    """대상 테이블마다 DELETE/INSERT를 조립한다.

    tables : 이관 대상 테이블(대문자, 정규화된 상태로 들어옴)
    pk_map : {테이블 → PK 컬럼 목록}. all_tables 딕셔너리 조회 결과(신뢰 출처).
    keys   : {컬럼 → 입력 조건}. 사용자가 화면에서 입력한 값(op=eq/between).
    from_link/to_link : SELECT 소스 / DELETE·INSERT 대상 DB 링크.

    반환: 전체 sql + 생성/제외 분류(generated/skipped/no_pk) + 접미사 그룹(groups).
    한 테이블도 자기 PK 컬럼 중 값이 채워진 것만 WHERE로 쓰며, 판정 규칙은 아래 두 continue.
    """
    from_at = _at(from_link)   # SELECT 소스(원격지)
    to_at = _at(to_link)       # DELETE/INSERT 대상

    blocks: list[str] = []       # 생성된 테이블 블록(전체 sql 조립용)
    generated: list[str] = []    # SQL이 만들어진 테이블
    skipped_list: list[str] = []      # 판정②: PK는 있으나 매칭 값 0개 → 제외(전체 삭제 방지)
    no_pk_list: list[str] = []        # 판정①: PK 컬럼 자체가 없음 → 제외
    group_blocks: dict[str, list[str]] = {}   # 그룹키 → 블록들
    group_tables: dict[str, list[str]] = {}   # 그룹키 → 테이블들

    for t in tables:
        # 판정①: 딕셔너리에 이 테이블의 PK 컬럼이 없으면 WHERE를 만들 수 없음 → no_pk
        cols = pk_map.get(t) or []
        if not cols:
            no_pk_list.append(t)
            continue

        # 이 테이블의 PK 컬럼마다 입력 값이 있으면 조건 생성, 없으면 omitted(조건절에서 제외)
        conds: list[str] = []
        omitted: list[str] = []
        for col in cols:
            kc = keys.get(col)
            cond = _condition(col, kc) if kc else None
            if cond:
                conds.append(cond)
            else:
                omitted.append(col)

        # 판정②: 채워진 조건이 하나도 없으면 WHERE 없는 DELETE = 전체 삭제 → 안전상 제외
        if not conds:
            skipped_list.append(t)
            continue

        # WHERE 절 조립(첫 조건은 " WHERE ", 나머지는 "   AND "로 이어 붙임). DELETE·INSERT가 공유.
        where = "\n".join(
            (" WHERE " if i == 0 else "   AND ") + c for i, c in enumerate(conds)
        )
        om = f"  (미입력 조건 제외: {', '.join(omitted)})" if omitted else ""
        # DELETE는 TO(대상)에서, INSERT는 FROM(원격 소스)에서 읽어 TO에 넣는다.
        block = (
            f"-- {t}{om}\n"
            f"DELETE FROM {t}{to_at}\n{where};\n"
            f"INSERT INTO {t}{to_at}\nSELECT * FROM {t}{from_at}\n{where};"
        )
        blocks.append(block)
        generated.append(t)

        # 접미사(_BS/_HT/...)별로 블록을 모아 둔다(팝업 그룹 박스용)
        gk = _group_key(t)
        group_blocks.setdefault(gk, []).append(block)
        group_tables.setdefault(gk, []).append(t)

    # 전체 sql 상단에 붙일 제외 안내 주석
    notes: list[str] = []
    if no_pk_list:
        notes.append("-- (PK 정보 없어 제외) " + ", ".join(no_pk_list))
    if skipped_list:
        notes.append("-- (입력한 키가 없어 제외: 전체 삭제 방지) " + ", ".join(skipped_list))

    # 전체 sql = 제외 주석 + 생성 블록 전부('전체 복사'용)
    parts: list[str] = []
    if notes:
        parts.append("\n".join(notes))
    if blocks:
        parts.append("\n\n".join(blocks))

    # 그룹 순서: GROUP_ORDER 먼저, 마지막에 기타. 비어 있는 그룹은 제외.
    groups: list[MigrationGroup] = []
    for gk in GROUP_ORDER + [GROUP_OTHER]:
        if group_blocks.get(gk):
            groups.append(MigrationGroup(
                key=gk,
                sql="\n\n".join(group_blocks[gk]),
                tables=group_tables[gk],
            ))

    return MigrationResult(
        sql="\n\n".join(parts),
        generated=generated,
        skipped=skipped_list,
        no_pk=no_pk_list,
        groups=groups,
    )
