"""Impact Analysis 오케스트레이션.

입력(현재는 테이블명)으로부터 영향 범위를 역방향으로 추적한다. table_extractor가 식별자로
원격 파일을 읽어 "무엇을 참조하는가"(정방향)를 구한다면, 여기는 "누가 나를 참조하는가"(역방향)를
구한다 — 역방향은 ID 1건 조회로 안 되고 코퍼스를 훑어야 하므로, 원격 grep으로 후보를 좁힌 뒤
파싱으로 확정하는 2단계를 쓴다(현재 구현은 1홉의 후보 단계까지).

라우터가 얇게 유지되도록 도메인 조회(proframe)를 여기서 호출해 묶는다.
"""
from __future__ import annotations

import logging

from app.common.io.ssh import CommandRunner
from app.common.proframe.dbio import find_dbios_referencing

logger = logging.getLogger("no_gada.impact_analysis")


def find_dbios(table: str, searcher: CommandRunner) -> list[str]:
    """테이블을 참조하는 DBIO ID 후보 목록(1홉의 후보 단계).

    원격 grep으로 좁힌 느슨한 후보다 — 파싱 확정은 후속 단계에서 붙인다.
    """
    ident = table.strip()
    dbios = find_dbios_referencing(ident, searcher)
    logger.info("find_dbios: table=%s → DBIO 후보 %d개", ident, len(dbios))
    return dbios
