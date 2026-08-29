"""Impact Analysis 오케스트레이션.

입력(현재는 테이블명)으로부터 영향 범위를 역방향으로 추적한다. table_extractor가 식별자로
원격 파일을 읽어 "무엇을 참조하는가"(정방향)를 구한다면, 여기는 "누가 나를 참조하는가"(역방향)를
구한다 — 역방향은 ID 1건 조회로 안 되고 코퍼스를 훑어야 하므로, 원격 grep으로 후보를 좁힌 뒤
파싱으로 확정하는 2단계를 쓴다(1홉 grep 후보 → 2홉 파싱 확정).

라우터가 얇게 유지되도록 도메인 조회(proframe)를 여기서 호출해 묶는다.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

from app.common.io.sftp import SourceNotFound, SourceReader
from app.common.io.ssh import CommandRunner, grep_files
from app.common.parse.sql import ExtractionError
from app.common.proframe.dbio import UnknownSqlType, dbio_referenced_tables, find_dbios_referencing
from app.common.proframe.module_source import COMPILE_ROOT, parse_module_path
from app.common.proframe.refs import scan_module_refs

logger = logging.getLogger("no_gada.impact_analysis")

# "누가 이걸 호출하는가"를 물을 수 있는 참조 타입 — service/batch는 항상 최상위(누가 부르는지
# 추적할 대상이 아님)라 dbio/biz 둘뿐이다. Module_Type(4종) 전체가 아니라 이 2종으로 좁힘.
CallerRefType = Literal["dbio", "biz"]


@dataclass
class CallersResult:
    services: list[str] = field(default_factory=list)
    bizs: list[str] = field(default_factory=list)
    batches: list[str] = field(default_factory=list)


def find_dbios(table: str, searcher: CommandRunner, reader: SourceReader) -> list[str]:
    """테이블을 참조하는 DBIO ID 확정 목록(1홉 grep 후보 → 2홉 파싱 확정).

    grep은 부분 문자열 매칭이라 오탐(다른 테이블명과 접두사가 겹치는 등)이 섞일 수 있다.
    각 후보의 DBIO XML을 실제로 파싱해 SQL이 정말 이 테이블을 참조하는지 확정한다.
    파일 부재(SourceNotFound)·SQLTYPE 미인식(UnknownSqlType)·파싱 실패(ExtractionError)는
    그 후보만 skip(부분성공) — 원격 접속 자체 실패(SourceError)는 결과를 숨기지 않고
    그대로 전파해 호출부(라우터)가 503으로 보고하게 한다.
    """
    ident = table.strip()
    candidates = find_dbios_referencing(ident, searcher)
    logger.info("find_dbios: table=%s → grep 후보 %d개", ident, len(candidates))

    target = ident.upper()
    confirmed: list[str] = []
    for dbio_id in candidates:
        try:
            tables, _ = dbio_referenced_tables(dbio_id, reader)
        except SourceNotFound:
            logger.debug("find_dbios: 후보 skip(파일 없음) dbio_id=%s", dbio_id)
            continue
        except (UnknownSqlType, ExtractionError) as e:
            logger.warning("find_dbios: 후보 skip(파싱 실패) dbio_id=%s: %s", dbio_id, e)
            continue
        if target in tables:
            confirmed.append(dbio_id)

    logger.info("find_dbios: table=%s → 확정 %d개", ident, len(confirmed))
    return confirmed


def find_callers(
    ref_type: CallerRefType,
    ref_id: str,
    searcher: CommandRunner,
    reader: SourceReader,
    resource_groups: list[str] | None = None,
) -> CallersResult:
    """(참조 타입, ID)를 실제로 호출하는 biz/service/batch 모듈 확정 목록(1홉 grep 후보 →
    2홉 파싱 확정). DBIO("DBIO가 어디서 호출되나")와 Biz("이 Biz는 누가 부르나, 재귀용")
    둘 다 이 함수 하나로 처리한다 — grep·경로 판별·파싱 확정 파이프라인이 완전히 동일하고,
    `scan_module_refs`가 돌려주는 `(타입, ID)` 튜플에서 어떤 타입을 찾느냐만 다르다.

    `resource_groups`를 주면 그 업무그룹들 밑에서만 grep해 범위를 좁힌다(비어 있으면 전체
    업무그룹 대상 — `COMPILE_ROOT` 하나로 재귀 grep 한 번이면 다 커버됨). `word=True`로
    단어 경계 매칭을 써서(`find_dbios`의 테이블명 느슨한 부분일치보다 타이트하게) — ID는
    항상 `"ID"`처럼 따옴표로 감싸여 호출되므로 안전하고 더 정확하다.

    각 grep 히트 경로를 `parse_module_path`로 판별(규약과 안 맞으면 skip) → 그 경로를
    그대로 읽어(경로 재조합 없이 오차 원천 차단) `scan_module_refs`로 파싱, `(ref_type, ID)`가
    실제로 있을 때만 확정(같은 문자열이 주석·다른 문맥에 우연히 있는 오탐을 거름).
    `SourceNotFound`는 그 후보만 skip(부분성공) — `SourceError`는 `find_dbios`와 동일하게
    그대로 전파해 호출부가 503으로 보고하게 한다.
    """
    ident = ref_id.strip()

    if resource_groups:
        hits: list[str] = []
        for group in resource_groups:
            hits.extend(grep_files(searcher, ident, f"{COMPILE_ROOT}/{group}", word=True))
    else:
        hits = grep_files(searcher, ident, COMPILE_ROOT, word=True)
    logger.info("find_callers: %s=%s → grep 후보 %d개", ref_type, ident, len(hits))

    result = CallersResult()
    for path in hits:
        parsed = parse_module_path(path)
        if parsed is None:
            continue
        module_type, _resource_group, file_id = parsed

        try:
            src = reader.read(path)
        except SourceNotFound:
            logger.debug("find_callers: 후보 skip(파일 없음) path=%s", path)
            continue

        if (ref_type, ident) not in scan_module_refs(src):
            continue

        if module_type == "service":
            result.services.append(file_id)
        elif module_type == "biz":
            result.bizs.append(file_id)
        elif module_type == "batch":
            result.batches.append(file_id)

    result.services = sorted(set(result.services))
    result.bizs = sorted(set(result.bizs))
    result.batches = sorted(set(result.batches))
    logger.info(
        "find_callers: %s=%s → 확정 service=%d biz=%d batch=%d",
        ref_type, ident, len(result.services), len(result.bizs), len(result.batches),
    )
    return result
