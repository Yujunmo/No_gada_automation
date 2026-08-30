"""C 소스 텍스트 → 타입 포함 참조 스캔 (dbio_sql.py의 자매).

service/batch/biz 모듈 C 소스 안에서 다른 모듈/DBIO를 참조하는 콜 매크로를 찾는다. 콜
매크로 자체가 대상 타입을 알려주므로(`pfmDbio*`=dbio, `pfmDlCall`=biz,
`pfmServiceModuleCall`=service) ID 접두로 타입을 추정할 필요가 없다(업무그룹 7종 밖의
접두도 있어 접두 분류는 신뢰 불가).

batch만 예외: 전용 콜 매크로가 없다. 배치는 항상 고정된 biz 모듈
`pfmDlCall("MZPFM_BatchLinkCall", ...)`를 통해서만 간접 호출되고, 실제 대상 배치 ID는
콜 인자가 아니라 그 직전 별도 대입문의 문자열 리터럴(`STRCPY(temporaryInput.bat_code,
"B<업무그룹4자리><suffix>")`)로 하드코딩돼 있다. 그래서 batch만 콜 매크로 인자 위치가
아니라 파일 전체를 리터럴 패턴으로 스캔한다. 이때 `pfmDlCall("MZPFM_BatchLinkCall", ...)`
자체도 biz 규칙에 걸려 `("biz", "MZPFM_BatchLinkCall")`로 같이 나오는데, 그 이름의 소스
파일은 없어 재귀 중 SourceNotFound로 skip되는 게 의도된 동작이다(부분 성공).

ProFrame 코드젠은 실행되지 않는 예시 코드를 `//`/`/* */`로 통째로 주석 처리해 남겨두는데
그 안에도 콜 매크로 형태 그대로인 죽은 코드가 들어 있어(실물 SPCSP53619C.c 450번 줄 실증)
정규식 매칭 전 `c_source.strip_comments`로 주석을 반드시 제거한다.

table_extractor가 정방향(모듈 소스 → 그 모듈이 참조하는 것)에 먼저 쓰지만, impact_analysis의
역방향(어떤 ID를 참조하는 후보 소스를 찾은 뒤, 정말 참조하는지 확정)도 같은 파싱이 필요해
공용에 둔다.
"""
from __future__ import annotations

import logging
import re
from typing import get_args

from app.common.parse.c_source import strip_comments
from app.common.proframe.types import Module_Type, ResourceGroup

logger = logging.getLogger("no_gada.table_extractor")

# pfmDbio<Select|OpenCursorArray|Dml|...>("ID") — 첫 문자열 인자가 DBIO ID.
_DBIO_RE = re.compile(r'pfmDbio\w*\(\s*"([A-Z0-9_]+)"')
# pfmDlCall("ID", "ID", ...) — 첫 문자열 인자가 biz ID.
_BIZ_RE = re.compile(r'pfmDlCall\(\s*"([A-Za-z0-9_]+)"')
# pfmServiceModuleCall(&in, &out, &linkHeader, sizeof(ID_IN), ...) — 구조체명에서 ID 추출.
_SERVICE_RE = re.compile(r'pfmServiceModuleCall\([\s\S]{0,300}?sizeof\(\s*([A-Za-z]\w*)_IN\b')
# "B<업무그룹4자리><suffix>" — 콜 매크로 인자가 아니라 파일 전체 리터럴 스캔.
# 업무그룹 7종은 types.py의 ResourceGroup이 유일한 소스 — 여기서 하드코딩하지 않고 끌어온다.
_RESOURCE_GROUP_ALT = "|".join(get_args(ResourceGroup))
_BATCH_RE = re.compile(rf'"(B(?:{_RESOURCE_GROUP_ALT})[A-Z0-9]+)"')

_PATTERNS: tuple[tuple[Module_Type, "re.Pattern[str]"], ...] = (
    ("dbio", _DBIO_RE),
    ("biz", _BIZ_RE),
    ("service", _SERVICE_RE),
    ("batch", _BATCH_RE),
)


def scan_module_refs(text: str) -> list[tuple[Module_Type, str]]:
    """C 소스 텍스트에서 (타입, ID) 참조를 등장 순서대로, 중복 제거해 뽑는다."""
    cleaned, removed = strip_comments(text)
    if removed:
        logger.debug("scan_module_refs: 주석 %d개 제거", removed)

    matches: list[tuple[int, Module_Type, str]] = []
    for ref_type, pattern in _PATTERNS:
        for m in pattern.finditer(cleaned):
            matches.append((m.start(), ref_type, m.group(1)))
    matches.sort(key=lambda item: item[0])

    # 중복 제거: (타입, ID) 쌍이 이미 나오면 skip. 순서 유지.
    seen: set[tuple[Module_Type, str]] = set()
    refs: list[tuple[Module_Type, str]] = []
    for _, ref_type, ref_id in matches:
        key = (ref_type, ref_id)
        if key in seen:
            continue
        seen.add(key)
        refs.append(key)
    return refs
