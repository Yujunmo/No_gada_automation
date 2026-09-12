"""ProFrame 모듈 ID → 원격 소스 조회 (app/tools/support/).

Data Migration의 "추출경로"/"발견된 batch" 목록에서 항목의 읽기 버튼을 누르면 호출된다.
특정 툴 전용이 아니라(Impact Analysis도 같은 조회가 필요해질 것) 사이드바 도구가 아닌
부가 API라 app/tools/support/에 둔다 — 라우터는 FastAPI에 의존하므로 app/common/(HTTP를
전혀 모르는 층)에는 둘 수 없다.

조회 자체는 app/common/의 기존 함수(dbio.read_dbio_xml / module_source.read_module_source)를
그대로 쓴다. 이 모듈은 HTTP 경계(경로 파라미터 검증, 크기 가드, 예외→상태코드 매핑)만 담당한다.

성능 메모: default_reader가 yield 의존성이라 **요청마다 SFTP 세션을 새로 맺고 응답 후 닫는다**.
재귀 추출은 그 접속 하나를 수백 번의 read가 나눠 쓰지만 이 엔드포인트는 read 한 번이 접속
하나를 통째로 부담한다 — 즉 여기서 체감하는 지연의 대부분은 경로 탐색이 아니라 SSH 핸드셰이크다
(반복 클릭 비용은 프론트 캐시가 흡수한다).
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.common.io.sftp import SourceError, SourceNotFound, SourceReader, default_reader
from app.common.proframe import Module_Type, dbio_sql
from app.common.proframe.dbio import UnknownSqlType, read_dbio_xml
from app.common.proframe.module_source import load_group_map, read_module_source

# 로거 이름은 no_gada.source가 아니라 no_gada.support — 전자는 이미 app/common/io/sftp.py가
# 쓰고 있어서, 같은 이름을 쓰면 SFTP I/O 로그와 이 라우터 로그가 구분되지 않는다.
logger = logging.getLogger("no_gada.support")

router = APIRouter(prefix="/source")

# 응답 본문 상한. 초과분은 잘라 보내고 truncated로 알린다 — 413으로 막으면 앞부분조차 못 보는데,
# "소스 보기"는 잘린 앞부분이라도 읽는 게 목적에 맞다.
MAX_SOURCE_CHARS = 1_000_000


class SourceResponse(BaseModel):
    module_type: str
    file_id: str
    content: str       # dbio면 추출된 SQL, 그 외는 C 소스 원문
    truncated: bool    # MAX_SOURCE_CHARS를 넘어 잘렸는지


def _read_dbio_sql(file_id: str, reader: SourceReader) -> str:
    """DBIO ID → XML 조회 → <sqlString> 추출 → `;`로 연결.

    공용 `dbio.dbio_referenced_tables`를 쓰지 않는 이유: 그 함수는 내부에서
    `extract_tables`(sqlglot)를 돌려 `ExtractionError`를 던질 수 있다. **파싱이 안 되는
    SQL일수록 사람이 눈으로 봐야 하는데** 그걸 못 보게 막는 꼴이 된다. 이 조합은
    sqlglot을 아예 타지 않으므로 어떤 SQL이든 내용은 항상 돌려준다.

    `<sqlString>`이 하나도 없으면 빈 문자열을 돌려준다(에러 아님 — 프론트가 빈 상태로 표시).
    """
    xml_text = read_dbio_xml(file_id, reader)
    return ";\n".join(dbio_sql.extract_sql(xml_text))


@router.get("/{module_type}/{file_id}", response_model=SourceResponse)
def read_source(
    module_type: Module_Type,
    file_id: str,
    request: Request,
    resource_group: Optional[str] = None,
    reader: SourceReader = Depends(default_reader),
) -> SourceResponse:
    """module_type/ID (+업무그룹) → 원격 소스 내용.

    `module_type`은 Literal이라 잘못된 값은 FastAPI가 422로 자동 거부한다.
    `resource_group`은 **옵셔널 쿼리 파라미터**다 — 추출경로에 뜨는 ID는 대부분 재귀 중
    발견된 것이라 프론트가 업무그룹을 모르고, read_module_source가 group_map/find 폴백으로
    알아서 찾는다. 추측해서 넘기면 오히려 해롭다(값이 주어지면 폴백 없이 그 경로만 읽고 404).
    """
    ident = file_id.strip()
    logger.info("read_source 요청 수신: module_type=%s resource_group=%s file_id=%s",
                module_type, resource_group, ident)

    if not ident:
        logger.warning("read_source 거부: 빈 ID")
        raise HTTPException(status_code=400, detail="file_id is empty")

    if resource_group is not None and resource_group not in request.app.state.resource_groups:
        logger.warning("read_source 거부: 유효하지 않은 resource_group=%s", resource_group)
        raise HTTPException(status_code=422, detail=f"Unknown resource group: {resource_group}")

    try:
        if module_type == "dbio":
            content = _read_dbio_sql(ident, reader)
        else:
            # group_map을 반드시 넘긴다 — 없으면 매 요청이 업무그룹 전수 탐색(listdir + 그룹 수만큼
            # read 시도)으로 떨어진다. 단 batch는 build_group_map이 service/biz만 순회하므로
            # 매핑에 절대 없고, 따라서 batch 조회는 항상 find 폴백을 탄다("batch만 느림"의 원인).
            content = read_module_source(
                module_type, ident, reader,
                resource_group=resource_group,
                group_map=load_group_map(),
            )
    except UnknownSqlType as e:
        logger.warning("read_source 거부(ID 패턴 인식 불가): %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except SourceNotFound as e:
        logger.warning("read_source 실패(파일 없음): %s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except SourceError as e:
        logger.warning("read_source 실패(원격 접속): %s", e)
        raise HTTPException(status_code=503, detail=str(e))

    truncated = len(content) > MAX_SOURCE_CHARS
    if truncated:
        logger.info("read_source 절단: %d chars → %d chars file_id=%s",
                    len(content), MAX_SOURCE_CHARS, ident)
        content = content[:MAX_SOURCE_CHARS]

    logger.info("read_source 완료: module_type=%s file_id=%s (%d chars, truncated=%s)",
                module_type, ident, len(content), truncated)
    return SourceResponse(
        module_type=module_type, file_id=ident, content=content, truncated=truncated
    )
