"""Table Extractor의 "항상 제외" 목록 2종 (둘 다 설정 파일 기반, 형식은 동일, 조회+저장 모두 지원).

1. 재귀 참조 제외(load_excluded_refs/save_excluded_refs): service.extract_from_module이
   소스를 재귀적으로 훑다가 "만나는" DBIO/모듈 ID 참조를 거른다(dbio/biz/service/batch
   타입 무관 — ID 하나로 통일 체크). 최상위(GET /table-extractor/...)로 직접 요청된 ID는
   이 목록과 무관하게 항상 처리된다. Table Extractor 설정 팝업의 "모듈 예외처리" 탭이
   save_excluded_refs로 저장한다.
2. 테이블 제외(load_excluded_tables/save_excluded_tables): service.extract()가 최종적으로
   return하는 tables 목록에서 항상 제외할 물리 테이블명. 재귀 탐색 중 만나는 참조가 아니라
   최종 결과에만 적용된다. 설정 팝업의 "테이블 추출 예외처리" 탭이 저장한다.

둘 다 저장은 전체 교체 방식이다(UI가 항상 완전한 목록을 들고 있다가 저장하는 구조라 부분
추가/삭제 API는 두지 않는다). 유일한 차이는 정규화: 테이블명은 시스템 전체가 대문자 규약이라
저장/조회 시 대문자화하지만, ID는 재귀 중 매칭이 대소문자 구분이라 원래 대소문자를 그대로 보존한다.

이 파일이 읽고 쓰는 설정 파일은 devops/UI가 로컬 텍스트 편집기로도 직접 열어볼 수 있으므로,
`NOGADA_SOURCE_ENCODING`(기본 `utf-8`, `io/sftp.py`·`io/ssh.py`의 원격 소스 디코딩과 같은 env)을
그대로 따른다 — 회사 환경 인코딩에 맞춰 반입 시 이 env 하나만 바꾸면 전부 일관되게 전환된다.
"""
from __future__ import annotations

import logging
import os
from typing import Iterable

logger = logging.getLogger("no_gada.table_extractor")

DEFAULT_EXCLUDED_REFS_PATH = "config/excluded_refs.txt"
DEFAULT_EXCLUDED_TABLES_PATH = "config/excluded_tables.txt"


def _text_encoding() -> str:
    return os.environ.get("NOGADA_SOURCE_ENCODING", "utf-8")


def _write_names(path: str, names: set[str]) -> None:
    """정규화된 이름 집합을 정렬해서 파일에 통째로 덮어쓴다(save_excluded_* 공용 저장 로직)."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding=_text_encoding()) as f:
        for name in sorted(names):
            f.write(name + "\n")


def _resolve_excluded_refs_path(path: str | None) -> str:
    return path if path is not None else os.environ.get("NOGADA_EXCLUDED_REFS_PATH", DEFAULT_EXCLUDED_REFS_PATH)


def load_excluded_refs(path: str | None = None) -> set[str]:
    """설정 파일에서 제외 ID 집합을 읽는다.

    한 줄에 ID 하나, `#` 뒤는 주석, 빈 줄은 무시. 파일이 없으면 빈 set(선택적 기능이라
    미설정 시 아무것도 제외하지 않는 게 안전한 기본값).
    """
    path = _resolve_excluded_refs_path(path)
    if not os.path.isfile(path):
        return set()

    ids: set[str] = set()
    with open(path, encoding=_text_encoding()) as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line:
                ids.add(line)
    logger.debug("load_excluded_refs: %d개 로드 path=%s", len(ids), path)
    return ids


def save_excluded_refs(ids: Iterable[str], path: str | None = None) -> set[str]:
    """재귀 참조 제외 ID 목록을 설정 파일에 통째로 덮어쓴다(설정 팝업의 저장 버튼 → 전체 교체).

    ID는 대소문자를 그대로 보존한다(extract_from_module의 `ref_id in excluded` 매칭이
    대소문자 구분이라 테이블명과 달리 대문자로 정규화하면 매칭이 깨진다). 공백 제거·중복
    제거 후 정렬해서 저장. 반환값은 실제로 저장된 정규화 집합(라우터가 그대로 응답 바디로
    돌려줘 프론트 상태를 서버 저장 결과와 일치시킨다).
    """
    path = _resolve_excluded_refs_path(path)
    normalized = {i.strip() for i in ids if i.strip()}
    _write_names(path, normalized)
    logger.info("save_excluded_refs: %d개 저장 path=%s", len(normalized), path)
    return normalized


def _resolve_excluded_tables_path(path: str | None) -> str:
    return path if path is not None else os.environ.get("NOGADA_EXCLUDED_TABLES_PATH", DEFAULT_EXCLUDED_TABLES_PATH)


def load_excluded_tables(path: str | None = None) -> set[str]:
    """설정 파일에서 예외 테이블명 집합을 읽는다.

    이름은 대문자로 정규화(테이블명은 시스템 전체에서 대문자 규약)해 비교 시 대소문자 차이로
    누락되는 일이 없게 한다. 파일이 없으면 빈 set(미설정 시 아무것도 제외하지 않는 안전한 기본값).
    """
    path = _resolve_excluded_tables_path(path)
    if not os.path.isfile(path):
        return set()

    tables: set[str] = set()
    with open(path, encoding=_text_encoding()) as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line:
                tables.add(line.upper())
    logger.debug("load_excluded_tables: %d개 로드 path=%s", len(tables), path)
    return tables


def save_excluded_tables(tables: Iterable[str], path: str | None = None) -> set[str]:
    """예외 테이블명 목록을 설정 파일에 통째로 덮어쓴다(설정 팝업의 저장 버튼 → 전체 교체).

    공백 제거·대문자화 후 중복 제거·정렬해서 저장한다. 반환값은 실제로 저장된 정규화 집합
    (라우터가 그대로 응답 바디로 돌려줘 프론트 상태를 서버 저장 결과와 일치시킨다).
    """
    path = _resolve_excluded_tables_path(path)
    normalized = {t.strip().upper() for t in tables if t.strip()}
    _write_names(path, normalized)
    logger.info("save_excluded_tables: %d개 저장 path=%s", len(normalized), path)
    return normalized
