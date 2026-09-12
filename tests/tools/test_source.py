"""app/tools/support/source.py — GET /source/{module_type}/{file_id} 계약 테스트.

네트워크 없이(인메모리 fake reader) 라우팅·경로 파라미터 검증·예외 매핑·크기 가드를 고정한다.
픽스처는 remote_ssh_server/truap01dap1/의 실물 DBIO XML.

group_map은 반드시 테스트마다 경로를 지정한다(_isolate_group_map) — 지정하지 않으면
load_group_map()이 레포의 실제 config/module_group_map.txt를 읽어, 그 파일이 바뀔 때마다
테스트 결과가 흔들린다.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.common.io.sftp import SourceError, SourceNotFound, default_reader
from app.common.proframe import dbio
from app.common.proframe.module_source import COMPILE_ROOT, module_path
from app.main import app
from app.tools.support.source import MAX_SOURCE_CHARS

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "remote_ssh_server" / "truap01dap1" / "proframe" / "proframe5.0"
    / "release" / "dbio" / "xml"
)
DS200_ID = "PFO_STCK_MA_DS200"
DS200_XML = (FIXTURE_ROOT / f"pfmDbio{DS200_ID}.xml").read_text("utf-8")


def _dbio_path(file_id: str) -> str:
    return f"{dbio.DBIO_RESOURCE_ROOT}/{dbio.DBIO_FILENAME_PREFIX}{file_id}.xml"


class FakeReader:
    def __init__(self, files: dict[str, str], dirs: dict[str, list[str]] | None = None):
        self._files = files
        self._dirs = dirs or {}
        self.read_calls: list[str] = []
        self.listdir_calls: list[str] = []

    def read(self, path: str) -> str:
        self.read_calls.append(path)
        if path not in self._files:
            raise SourceNotFound(path)
        return self._files[path]

    def listdir(self, path: str) -> list[str]:
        self.listdir_calls.append(path)
        if path not in self._dirs:
            raise SourceNotFound(path)
        return self._dirs[path]


class BrokenReader:
    """접속 자체가 실패하는 reader — 파일 부재(404)와 구분되는 503 경로를 만든다."""

    def read(self, path: str) -> str:
        raise SourceError("SFTP 접속 실패: 127.0.0.1:2222")

    def listdir(self, path: str) -> list[str]:
        raise SourceError("SFTP 접속 실패: 127.0.0.1:2222")


client = TestClient(app)


@pytest.fixture(autouse=True)
def _fake_reader_override():
    # 기본은 빈 reader(무조건 SourceNotFound) — 테스트가 실제 SFTP에 붙는 것을 막는다.
    app.dependency_overrides[default_reader] = lambda: FakeReader({})
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _isolate_group_map(monkeypatch, tmp_path):
    # 기본은 "매핑 파일 없음" → load_group_map()이 {} 반환 → find 폴백 경로.
    # 레포의 실제 config/module_group_map.txt가 테스트에 새어 들어오지 않게 막는다.
    monkeypatch.setenv("NOGADA_MODULE_GROUP_MAP_PATH", str(tmp_path / "no_such_map.txt"))


@pytest.fixture(autouse=True)
def _init_app_state():
    app.state.resource_groups = ["NCOM", "NCSP", "PCOM", "PCSH", "PCSP", "PPFR", "RLGR"]
    yield


def _use_files(files: dict[str, str], dirs: dict[str, list[str]] | None = None) -> FakeReader:
    reader = FakeReader(files, dirs)
    app.dependency_overrides[default_reader] = lambda: reader
    return reader


# ---- 경로 파라미터 검증 (조회 전에 걸러지는 것들) ----

def test_unknown_module_type_rejected_by_literal():
    # Module_Type Literal에 없는 값 → FastAPI가 핸들러 진입 전에 422
    resp = client.get("/source/procedure/SOME_ID")
    assert resp.status_code == 422


def test_unknown_resource_group_rejected():
    resp = client.get("/source/service/SRLGR96602A", params={"resource_group": "ZZZZ"})
    assert resp.status_code == 422


def test_blank_file_id_rejected():
    # 공백만 있는 ID는 strip 후 빈 문자열 → 400 (조회를 시도하기 전에 거른다)
    resp = client.get("/source/dbio/%20%20")
    assert resp.status_code == 400


def test_file_id_is_stripped():
    _use_files({_dbio_path(DS200_ID): DS200_XML})
    resp = client.get(f"/source/dbio/%20{DS200_ID}%20")
    assert resp.status_code == 200
    assert resp.json()["file_id"] == DS200_ID


# ---- DBIO 분기 ----

def test_dbio_returns_extracted_sql():
    _use_files({_dbio_path(DS200_ID): DS200_XML})
    resp = client.get(f"/source/dbio/{DS200_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"module_type", "file_id", "content", "truncated"}
    assert body["module_type"] == "dbio"
    assert body["file_id"] == DS200_ID
    assert body["truncated"] is False
    # XML 원문이 아니라 <sqlString> 내용이 와야 한다
    assert "pfo_stck_ma" in body["content"].lower()
    assert "<sqlString>" not in body["content"]


def test_dbio_without_sqlstring_returns_empty_content():
    # <sqlString>이 없는 것은 에러가 아니다 — 프론트가 빈 상태 문구로 구분해 보여준다.
    _use_files({_dbio_path(DS200_ID): "<dynamicSqlQuery></dynamicSqlQuery>"})
    resp = client.get(f"/source/dbio/{DS200_ID}")
    assert resp.status_code == 200
    assert resp.json()["content"] == ""


def test_dbio_unparseable_sql_still_returned():
    """파싱 불가 SQL이어도 내용은 그대로 온다(sqlglot 미경유 회귀 고정).

    dbio_referenced_tables를 썼다면 내부 extract_tables가 ExtractionError를 던져 실패했을
    케이스 — 파싱이 안 되는 SQL일수록 사람이 눈으로 봐야 하므로 막히면 안 된다.
    """
    broken = "<dynamicSqlQuery><sqlString>SELECT FROM WHERE ))) 깨진 SQL</sqlString></dynamicSqlQuery>"
    _use_files({_dbio_path(DS200_ID): broken})
    resp = client.get(f"/source/dbio/{DS200_ID}")
    assert resp.status_code == 200
    assert "깨진 SQL" in resp.json()["content"]


def test_unknown_suffix_returns_400():
    # ID 끝 2글자가 SQLTYPE 매핑에 없음 → 파일없음(404)보다 명확한 400으로 먼저 거른다
    resp = client.get("/source/dbio/PFO_STCK_MA_ZZ001")
    assert resp.status_code == 400


def test_missing_file_returns_404():
    resp = client.get(f"/source/dbio/{DS200_ID}")   # 기본 빈 reader
    assert resp.status_code == 404


def test_source_error_returns_503():
    app.dependency_overrides[default_reader] = lambda: BrokenReader()
    resp = client.get(f"/source/dbio/{DS200_ID}")
    assert resp.status_code == 503


def test_oversized_content_is_truncated():
    big_sql = "A" * (MAX_SOURCE_CHARS + 500)
    _use_files({_dbio_path(DS200_ID): f"<dynamicSqlQuery><sqlString>{big_sql}</sqlString></dynamicSqlQuery>"})
    resp = client.get(f"/source/dbio/{DS200_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["truncated"] is True
    assert len(body["content"]) == MAX_SOURCE_CHARS


# ---- Service/Biz/Batch 분기 ----

SERVICE_ID = "SRLGR96602A"
SERVICE_SRC = "long SRLGR96602A(void) { pfmDbioSelect(); }"
GROUPS = ["PCSP", "RLGR", "PCOM"]


def test_service_with_resource_group_reads_directly():
    # 업무그룹을 알면 경로를 바로 조합한다 — 탐색(listdir) 없이 read 1회.
    path = module_path("service", "RLGR", SERVICE_ID)
    reader = _use_files({path: SERVICE_SRC})
    resp = client.get(f"/source/service/{SERVICE_ID}", params={"resource_group": "RLGR"})
    assert resp.status_code == 200
    assert resp.json()["content"] == SERVICE_SRC
    assert reader.read_calls == [path]
    assert reader.listdir_calls == []


def test_service_without_resource_group_uses_find_fallback():
    # 업무그룹을 모르면(재귀 중 발견된 참조가 이 경우) COMPILE_ROOT를 나열해 순차 탐색한다.
    path = module_path("service", "RLGR", SERVICE_ID)
    reader = _use_files({path: SERVICE_SRC}, {COMPILE_ROOT: GROUPS})
    resp = client.get(f"/source/service/{SERVICE_ID}")
    assert resp.status_code == 200
    assert resp.json()["content"] == SERVICE_SRC
    assert reader.listdir_calls == [COMPILE_ROOT]


def test_group_map_hit_skips_listdir(monkeypatch, tmp_path):
    # 매핑이 있으면 탐색 없이 바로 그 그룹 경로를 읽는다(find 폴백 가속의 요점).
    map_file = tmp_path / "map.txt"
    map_file.write_text(f"{SERVICE_ID}\tRLGR\tservice\n", encoding="utf-8")
    monkeypatch.setenv("NOGADA_MODULE_GROUP_MAP_PATH", str(map_file))

    path = module_path("service", "RLGR", SERVICE_ID)
    reader = _use_files({path: SERVICE_SRC}, {COMPILE_ROOT: GROUPS})
    resp = client.get(f"/source/service/{SERVICE_ID}")
    assert resp.status_code == 200
    assert reader.read_calls == [path]
    assert reader.listdir_calls == []


def test_biz_module_read():
    path = module_path("biz", "PCOM", "MPCOM_GetBzopDate")
    _use_files({path: "int main(void) {}"}, {COMPILE_ROOT: GROUPS})
    resp = client.get("/source/biz/MPCOM_GetBzopDate")
    assert resp.status_code == 200
    assert resp.json()["content"] == "int main(void) {}"


def test_batch_module_read_always_uses_find_fallback():
    """batch는 group_map에 절대 없다(build_group_map이 service/biz만 순회) → 항상 find 폴백."""
    path = module_path("batch", "RLGR", "BRLGRPRP0001")
    reader = _use_files({path: "int batch_main(void) {}"}, {COMPILE_ROOT: GROUPS})
    resp = client.get("/source/batch/BRLGRPRP0001")
    assert resp.status_code == 200
    assert reader.listdir_calls == [COMPILE_ROOT]


def test_module_not_found_in_any_group_returns_404():
    _use_files({}, {COMPILE_ROOT: GROUPS})
    resp = client.get("/source/biz/MPCOM_NoSuchModule")
    assert resp.status_code == 404


def test_module_source_error_returns_503():
    app.dependency_overrides[default_reader] = lambda: BrokenReader()
    resp = client.get(f"/source/service/{SERVICE_ID}")
    assert resp.status_code == 503
