"""app/tools/support/meta.py 단위 테스트.

app.state.resource_groups가 그대로 노출되는지만 고정한다(순수 조회, I/O·네트워크 없음).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EXPECTED_GROUPS = ["NCOM", "NCSP", "PCOM", "PCSH", "PCSP", "PPFR", "RLGR"]


@pytest.fixture(autouse=True)
def _init_app_state():
    app.state.resource_groups = EXPECTED_GROUPS
    yield


def test_resource_groups_from_app_state():
    resp = client.get("/meta/resource-groups")
    assert resp.status_code == 200
    assert resp.json() == {"resource_groups": EXPECTED_GROUPS}
