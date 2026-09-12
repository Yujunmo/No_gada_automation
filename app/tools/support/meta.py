"""특정 툴에 속하지 않는 공용 ProFrame 참조 데이터 조회 (app/tools/support/).

사이드바 도구가 아니라 여러 툴 프론트가 공유하는 부가 API라 app/tools/support/에 둔다
(app/tools/<name>/은 사이드바 도구 하나에 대응하는 규약). 라우터는 FastAPI에 의존하므로
app/common/(HTTP를 전혀 모르는 층)에는 둘 수 없다.

리소스그룹(업무그룹) 7종처럼 여러 툴 프론트가 각자 하드코딩해 쓰던 값을 백엔드
`app.common.proframe.types.ResourceGroup`(FastAPI 경로 검증이 이미 쓰는 그 Literal) 하나로
단일화한다 — 이 프로젝트가 빌드 스텝 없는 순수 정적 JS라 컴파일타임 주입이 불가능해서,
프론트가 페이지 로드 시 이 엔드포인트를 fetch해 목록을 받아오는 방식으로 동기화한다.
"""
from __future__ import annotations

from typing import get_args

from fastapi import APIRouter
from pydantic import BaseModel

from app.common.proframe.types import ResourceGroup

router = APIRouter(prefix="/meta")


class ResourceGroupsResponse(BaseModel):
    resource_groups: list[str]


@router.get("/resource-groups", response_model=ResourceGroupsResponse)
def resource_groups() -> ResourceGroupsResponse:
    return ResourceGroupsResponse(resource_groups=list(get_args(ResourceGroup)))
