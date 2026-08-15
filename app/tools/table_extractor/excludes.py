"""재귀 참조 집계에서 항상 제외할 DBIO/모듈 ID 목록 (설정 파일 기반).

최상위(GET /table-extractor/...)로 직접 요청된 ID는 이 목록과 무관하게 항상 처리된다.
여기서 걸러지는 건 service.extract_from_module이 소스를 재귀적으로 훑다가 "만나는"
참조뿐이다(dbio/biz/service/batch 타입 무관 — ID 하나로 통일 체크).
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger("no_gada.table_extractor")

DEFAULT_EXCLUDED_REFS_PATH = "config/excluded_refs.txt"


def load_excluded_refs(path: str | None = None) -> set[str]:
    """설정 파일에서 제외 ID 집합을 읽는다.

    한 줄에 ID 하나, `#` 뒤는 주석, 빈 줄은 무시. 파일이 없으면 빈 set(선택적 기능이라
    미설정 시 아무것도 제외하지 않는 게 안전한 기본값).
    """
    path = path if path is not None else os.environ.get("NOGADA_EXCLUDED_REFS_PATH", DEFAULT_EXCLUDED_REFS_PATH)
    if not os.path.isfile(path):
        return set()

    ids: set[str] = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line:
                ids.add(line)
    logger.debug("load_excluded_refs: %d개 로드 path=%s", len(ids), path)
    return ids
