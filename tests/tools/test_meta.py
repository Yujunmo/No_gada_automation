"""app/tools/meta/router.py 단위 테스트.

ResourceGroup Literal이 그대로 노출되는지만 고정한다(순수 조회, I/O·네트워크 없음).
"""
from __future__ import annotations

from typing import get_args

from fastapi.testclient import TestClient

from app.common.proframe.types import ResourceGroup
from app.main import app

client = TestClient(app)


def test_resource_groups_matches_literal():
    resp = client.get("/meta/resource-groups")
    assert resp.status_code == 200
    assert resp.json() == {"resource_groups": list(get_args(ResourceGroup))}
