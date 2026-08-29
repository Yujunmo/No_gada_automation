"""
Impact Analysis 회귀 테스트.

FakeSearcher(CommandRunner)로 원격 grep 후보를, FakeReader(SourceReader)로 원격 DBIO XML
조회를 인메모리로 대체해 네트워크 없이 확정 파싱 파이프라인(1홉 grep 후보 → 2홉 파싱 확정)을
검증한다.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.common.io.sftp import SourceError, SourceNotFound, default_reader
from app.common.io.ssh import CommandResult, SshError, default_command_runner
from app.common.proframe import dbio
from app.common.proframe.module_source import COMPILE_ROOT, module_path
from app.main import app
from app.tools.impact_analysis import service

client = TestClient(app)


class FakeSearcher:
    def __init__(self, hits: list[str] | None = None, *, raise_error: bool = False):
        self._hits = hits or []
        self._raise_error = raise_error
        self.run_calls: list[list[str]] = []

    def run(self, argv: list[str], *, timeout: int | None = None) -> CommandResult:
        self.run_calls.append(argv)
        if self._raise_error:
            raise SshError("grep 실패: boom")
        if not self._hits:
            return CommandResult(stdout="", stderr="", exit_code=1)
        return CommandResult(stdout="\n".join(self._hits) + "\n", stderr="", exit_code=0)


class FakeReader:
    def __init__(self, files: dict[str, str] | None = None, *, raise_error_for: set[str] | None = None):
        self._files = files or {}
        self._raise_error_for = raise_error_for or set()
        self.read_calls: list[str] = []

    def read(self, path: str) -> str:
        self.read_calls.append(path)
        if path in self._raise_error_for:
            raise SourceError(f"접속 실패: {path}")
        if path not in self._files:
            raise SourceNotFound(path)
        return self._files[path]

    def listdir(self, path: str) -> list[str]:
        raise SourceNotFound(path)


def _synth_dbio_xml(table: str) -> str:
    return f"<dynamicSqlQuery><sqlString>SELECT * FROM {table}</sqlString></dynamicSqlQuery>"


def _path(dbio_id: str) -> str:
    return f"{dbio.DBIO_RESOURCE_ROOT}/{dbio.DBIO_FILENAME_PREFIX}{dbio_id}.xml"


# ---- service.find_dbios ----

def test_find_dbios_confirms_true_positive_and_drops_false_positive():
    # grep은 부분 문자열이라 PFO_FUND_BS를 찾을 때 진짜 참조(real_id)와 오탐(fake_id, grep만
    # 걸리고 실제 SQL은 다른 테이블을 참조)이 둘 다 후보로 나온다 — 확정 파싱이 오탐을 걸러야 한다.
    real_id = "PFO_FUND_BS_DF001"
    fake_id = "PFO_FUND_BS_DF002"
    searcher = FakeSearcher([_path(real_id), _path(fake_id)])
    reader = FakeReader({
        _path(real_id): _synth_dbio_xml("PFO_FUND_BS"),
        _path(fake_id): _synth_dbio_xml("PFO_OTHER_TABLE"),
    })

    result = service.find_dbios("PFO_FUND_BS", searcher, reader)

    assert result == [real_id]


def test_find_dbios_skips_candidate_on_source_not_found():
    ok_id = "PFO_FUND_BS_DF001"
    missing_id = "PFO_FUND_BS_DF002"
    searcher = FakeSearcher([_path(ok_id), _path(missing_id)])
    reader = FakeReader({_path(ok_id): _synth_dbio_xml("PFO_FUND_BS")})  # missing_id는 파일 없음

    result = service.find_dbios("PFO_FUND_BS", searcher, reader)

    assert result == [ok_id]


def test_find_dbios_propagates_source_error():
    dbio_id = "PFO_FUND_BS_DF001"
    searcher = FakeSearcher([_path(dbio_id)])
    reader = FakeReader(raise_error_for={_path(dbio_id)})

    with pytest.raises(SourceError):
        service.find_dbios("PFO_FUND_BS", searcher, reader)


def test_find_dbios_empty_candidates_returns_empty_without_reading():
    searcher = FakeSearcher([])
    reader = FakeReader({})

    result = service.find_dbios("NO_SUCH_TABLE", searcher, reader)

    assert result == []
    assert reader.read_calls == []


# ---- service.find_dbio_callers ----

def _caller_src(dbio_id: str) -> str:
    return f'void Run() {{ pfmDbioSelect("{dbio_id}"); }}'


def test_find_dbio_callers_confirms_true_positive_and_drops_false_positive():
    # grep은 부분 문자열이라 실제 콜 매크로로 호출하는 모듈(real)과 주석 등에 문자열만
    # 우연히 존재하는 모듈(fake)이 둘 다 후보로 나온다 — 확정 파싱이 오탐을 걸러야 한다.
    dbio_id = "PFO_STCK_MA_DS200"
    real_path = module_path("biz", "PCOM", "MPCOM_Real")
    fake_path = module_path("biz", "PCOM", "MPCOM_Fake")
    searcher = FakeSearcher([real_path, fake_path])
    reader = FakeReader({
        real_path: _caller_src(dbio_id),
        fake_path: f"void Run() {{ /* {dbio_id} mentioned only in a comment */ }}",
    })

    result = service.find_dbio_callers(dbio_id, searcher, reader)

    assert result.bizs == ["MPCOM_Real"]
    assert result.services == []
    assert result.batches == []


def test_find_dbio_callers_classifies_by_module_type():
    dbio_id = "PFO_STCK_MA_DS200"
    biz_path = module_path("biz", "PCOM", "MPCOM_Biz")
    svc_path = module_path("service", "PCOM", "SVC_One")
    batch_path = module_path("batch", "PCOM", "BPCOM01")
    searcher = FakeSearcher([biz_path, svc_path, batch_path])
    reader = FakeReader({
        biz_path: _caller_src(dbio_id),
        svc_path: _caller_src(dbio_id),
        batch_path: _caller_src(dbio_id),
    })

    result = service.find_dbio_callers(dbio_id, searcher, reader)

    assert result.bizs == ["MPCOM_Biz"]
    assert result.services == ["SVC_One"]
    assert result.batches == ["BPCOM01"]


def test_find_dbio_callers_skips_path_not_matching_module_convention():
    searcher = FakeSearcher(["/some/unrelated/path.c"])
    reader = FakeReader({})

    result = service.find_dbio_callers("PFO_STCK_MA_DS200", searcher, reader)

    assert result.bizs == result.services == result.batches == []
    assert reader.read_calls == []


def test_find_dbio_callers_skips_candidate_on_source_not_found():
    path = module_path("biz", "PCOM", "MPCOM_Missing")
    searcher = FakeSearcher([path])
    reader = FakeReader({})  # 파일 없음

    result = service.find_dbio_callers("PFO_STCK_MA_DS200", searcher, reader)

    assert result.bizs == []


def test_find_dbio_callers_propagates_source_error():
    path = module_path("biz", "PCOM", "MPCOM_Err")
    searcher = FakeSearcher([path])
    reader = FakeReader(raise_error_for={path})

    with pytest.raises(SourceError):
        service.find_dbio_callers("PFO_STCK_MA_DS200", searcher, reader)


def test_find_dbio_callers_empty_candidates_returns_empty_without_reading():
    searcher = FakeSearcher([])
    reader = FakeReader({})

    result = service.find_dbio_callers("NO_SUCH_DBIO", searcher, reader)

    assert result.services == result.bizs == result.batches == []
    assert reader.read_calls == []


def test_find_dbio_callers_scopes_grep_to_resource_groups():
    dbio_id = "PFO_STCK_MA_DS200"
    searcher = FakeSearcher([])
    reader = FakeReader({})

    service.find_dbio_callers(dbio_id, searcher, reader, resource_groups=["PCOM", "NCOM"])

    assert searcher.run_calls == [
        ["grep", "-rlFiw", dbio_id, f"{COMPILE_ROOT}/PCOM"],
        ["grep", "-rlFiw", dbio_id, f"{COMPILE_ROOT}/NCOM"],
    ]


# ---- router ----

@pytest.fixture(autouse=True)
def _fake_deps_override():
    app.dependency_overrides[default_command_runner] = lambda: FakeSearcher([])
    app.dependency_overrides[default_reader] = lambda: FakeReader({})
    yield
    app.dependency_overrides.clear()


def _use(searcher: FakeSearcher, reader: FakeReader) -> None:
    app.dependency_overrides[default_command_runner] = lambda: searcher
    app.dependency_overrides[default_reader] = lambda: reader


def test_router_dbios_confirms_and_filters():
    real_id = "PFO_FUND_BS_DF001"
    fake_id = "PFO_FUND_BS_DF002"
    _use(
        FakeSearcher([_path(real_id), _path(fake_id)]),
        FakeReader({
            _path(real_id): _synth_dbio_xml("PFO_FUND_BS"),
            _path(fake_id): _synth_dbio_xml("PFO_OTHER_TABLE"),
        }),
    )

    resp = client.get("/impact-analysis/dbios/PFO_FUND_BS")

    assert resp.status_code == 200
    assert resp.json() == {"table": "PFO_FUND_BS", "dbios": [real_id]}


def test_router_dbios_empty_table_rejected():
    resp = client.get("/impact-analysis/dbios/%20")  # strip 후 빈 문자열
    assert resp.status_code == 400


def test_router_dbios_grep_failure_returns_503():
    _use(FakeSearcher([], raise_error=True), FakeReader({}))
    resp = client.get("/impact-analysis/dbios/PFO_FUND_BS")
    assert resp.status_code == 503


def test_router_dbios_source_error_returns_503():
    dbio_id = "PFO_FUND_BS_DF001"
    _use(FakeSearcher([_path(dbio_id)]), FakeReader(raise_error_for={_path(dbio_id)}))
    resp = client.get("/impact-analysis/dbios/PFO_FUND_BS")
    assert resp.status_code == 503


# ---- router callers ----

def test_router_callers_confirms_and_classifies():
    dbio_id = "PFO_STCK_MA_DS200"
    biz_path = module_path("biz", "PCOM", "MPCOM_Biz")
    _use(FakeSearcher([biz_path]), FakeReader({biz_path: _caller_src(dbio_id)}))

    resp = client.get(f"/impact-analysis/callers/{dbio_id}")

    assert resp.status_code == 200
    assert resp.json() == {"dbio": dbio_id, "services": [], "bizs": ["MPCOM_Biz"], "batches": []}


def test_router_callers_empty_dbio_id_rejected():
    resp = client.get("/impact-analysis/callers/%20")  # strip 후 빈 문자열
    assert resp.status_code == 400


def test_router_callers_grep_failure_returns_503():
    _use(FakeSearcher([], raise_error=True), FakeReader({}))
    resp = client.get("/impact-analysis/callers/PFO_STCK_MA_DS200")
    assert resp.status_code == 503


def test_router_callers_source_error_returns_503():
    path = module_path("biz", "PCOM", "MPCOM_Err")
    _use(FakeSearcher([path]), FakeReader(raise_error_for={path}))
    resp = client.get("/impact-analysis/callers/PFO_STCK_MA_DS200")
    assert resp.status_code == 503


def test_router_callers_passes_resource_groups_query_param():
    dbio_id = "PFO_STCK_MA_DS200"
    searcher = FakeSearcher([])
    _use(searcher, FakeReader({}))

    resp = client.get(
        f"/impact-analysis/callers/{dbio_id}",
        params=[("resource_groups", "PCOM"), ("resource_groups", "NCOM")],
    )

    assert resp.status_code == 200
    assert searcher.run_calls == [
        ["grep", "-rlFiw", dbio_id, f"{COMPILE_ROOT}/PCOM"],
        ["grep", "-rlFiw", dbio_id, f"{COMPILE_ROOT}/NCOM"],
    ]
