"""특정 툴에 속하지 않는 공용 ProFrame 참조 데이터 조회 (app/tools/support/).

사이드바 도구가 아니라 여러 툴 프론트가 공유하는 부가 API라 app/tools/support/에 둔다
(app/tools/<name>/은 사이드바 도구 하나에 대응하는 규약). 라우터는 FastAPI에 의존하므로
app/common/(HTTP를 전혀 모르는 층)에는 둘 수 없다.

리소스그룹(업무그룹)을 main.py의 lifespan에서 SSH로 동적 로드하고, 이 엔드포인트를 통해
프론트에 노출한다 — 프론트가 페이지 로드 시 이 엔드포인트를 fetch해 UI를 동적으로 구성한다.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/meta")


class ResourceGroupsResponse(BaseModel):
    resource_groups: list[str]


@router.get("/resource-groups", response_model=ResourceGroupsResponse)
def resource_groups(request: Request) -> ResourceGroupsResponse:
    return ResourceGroupsResponse(resource_groups=request.app.state.resource_groups)
