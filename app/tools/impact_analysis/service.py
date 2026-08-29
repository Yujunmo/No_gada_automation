"""Impact Analysis 오케스트레이션.

입력(현재는 테이블명)으로부터 영향 범위를 역방향으로 추적한다. table_extractor가 식별자로
원격 파일을 읽어 "무엇을 참조하는가"(정방향)를 구한다면, 여기는 "누가 나를 참조하는가"(역방향)를
구한다 — 역방향은 ID 1건 조회로 안 되고 코퍼스를 훑어야 하므로, 원격 grep으로 후보를 좁힌 뒤
파싱으로 확정하는 2단계를 쓴다(1홉 grep 후보 → 2홉 파싱 확정).

라우터가 얇게 유지되도록 도메인 조회(proframe)를 여기서 호출해 묶는다.
"""
from __future__ import annotations

import logging

from app.common.io.sftp import SourceNotFound, SourceReader
from app.common.io.ssh import CommandRunner
from app.common.parse.sql import ExtractionError
from app.common.proframe.dbio import UnknownSqlType, dbio_referenced_tables, find_dbios_referencing

logger = logging.getLogger("no_gada.impact_analysis")


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
