"""
Table Extractor 회귀 테스트.

네트워크 없이(인메모리 fake reader) DBIO 추출 파이프라인 전체(dbio → dbio_sql → service → router)와
REST 계약(경로 파라미터 검증, 에러 매핑)을 고정한다. 픽스처는 remote_ssh_server/truap01dap1/의 실물 DBIO XML.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.common.proframe import dbio
from app.common.io.db import DbError, Params, Row, default_db
from app.common.proframe.module_source import COMPILE_ROOT, module_path
from app.common.io.sftp import SourceNotFound, default_reader
from app.main import app
from app.common.proframe import dbio_sql
from app.tools.table_extractor import service

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "remote_ssh_server" / "truap01dap1" / "proframe" / "proframe5.0"
    / "release" / "dbio" / "xml"
)
DS200_XML = (FIXTURE_ROOT / "pfmDbioPFO_STCK_MA_DS200.xml").read_text("utf-8")
EI901_XML = (FIXTURE_ROOT / "pfmDbioPFO_MNCM_CLCD_HT_EI901.xml").read_text("utf-8")

DS200_PATH = f"{dbio.DBIO_RESOURCE_ROOT}/{dbio.DBIO_FILENAME_PREFIX}PFO_STCK_MA_DS200.xml"
EI901_PATH = f"{dbio.DBIO_RESOURCE_ROOT}/{dbio.DBIO_FILENAME_PREFIX}PFO_MNCM_CLCD_HT_EI901.xml"


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


client = TestClient(app)


@pytest.fixture(autouse=True)
def _fake_reader_override():
    # 기본은 빈 reader(무조건 SourceNotFound) — 실네트워크 접속을 막는다.
    # 특정 파일이 필요한 테스트는 아래에서 다시 override해서 덮어쓴다.
    app.dependency_overrides[default_reader] = lambda: FakeReader({})
    yield
    app.dependency_overrides.clear()


def _use_files(files: dict[str, str], dirs: dict[str, list[str]] | None = None) -> None:
    app.dependency_overrides[default_reader] = lambda: FakeReader(files, dirs)


# ---- dbio_sql.extract_sql ----

def test_extract_sql_dynamicsql_root():
    sqls = dbio_sql.extract_sql(DS200_XML)
    assert len(sqls) == 1
    assert "pfo_stck_ma" in sqls[0].lower()


def test_extract_sql_execsql_root():
    sqls = dbio_sql.extract_sql(EI901_XML)
    assert len(sqls) == 1
    assert "pfo_mncm_clcd_ht" in sqls[0].lower()


# ---- dbio.classify_sqltype ----

@pytest.mark.parametrize(
    "id_, expected",
    [
        ("PFO_STCK_MA_DS200", "DYNAMICSQL"),
        ("PFO_FUND_BS_DF037", "DYNAMICSQL"),
        ("PFO_X_DI001", "DYNAMICSQL"),
        ("PFO_X_DU001", "DYNAMICSQL"),
        ("PFO_X_DD001", "DYNAMICSQL"),
        ("PFO_MNCM_CLCD_HT_EI901", "EXECSQL"),
        ("PFO_X_EU001", "EXECSQL"),
        ("PFO_X_ED001", "EXECSQL"),
        ("PFO_X_PI001", "PERSIST"),
        ("PFO_X_PU001", "PERSIST"),
        ("PFO_X_PD001", "PERSIST"),
        ("PFO_X_PS001", "PERSIST"),
        ("PFO_X_PF001", "PERSIST"),
        ("PFO_X_VF001", "VIEW"),
        ("PFO_X_VS001", "VIEW"),
    ],
)
def test_classify_sqltype(id_, expected):
    assert dbio.classify_sqltype(id_) == expected


def test_classify_sqltype_unknown_suffix_rejected():
    with pytest.raises(dbio.UnknownSqlType):
        dbio.classify_sqltype("PFO_X_ZZ001")


def test_classify_sqltype_no_digits_rejected():
    with pytest.raises(dbio.UnknownSqlType):
        dbio.classify_sqltype("PFO_STCK_MA")


# ---- dbio.read_dbio_xml ----

def test_read_dbio_xml_found():
    reader = FakeReader({DS200_PATH: DS200_XML})
    assert dbio.read_dbio_xml("PFO_STCK_MA_DS200", reader) == DS200_XML


def test_read_dbio_xml_not_found():
    reader = FakeReader({})
    with pytest.raises(SourceNotFound):
        dbio.read_dbio_xml("PFO_STCK_MA_DS200", reader)


# ---- service.extract_from_module (재귀) ----

COMPILE_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "remote_ssh_server" / "truap01dap1" / "proframe" / "proframe5.0" / "compile"
)
GETBZOPDATE_SRC = (COMPILE_FIXTURE_ROOT / "PCOM/src/module/MPCOM_GetBzopDate.c").read_text("utf-8")
GETBZOPDATE_PATH = module_path("biz", "PCOM", "MPCOM_GetBzopDate")
GETBZOPDATE_DBIO_IDS = [f"PFO_DATE_MNGM_BS_VS{n:03d}" for n in range(4, 12)]


def _synth_dbio_xml(table: str) -> str:
    return f"<dynamicSqlQuery><sqlString>SELECT * FROM {table}</sqlString></dynamicSqlQuery>"


def _getbzopdate_files() -> dict[str, str]:
    files = {GETBZOPDATE_PATH: GETBZOPDATE_SRC}
    for i, dbio_id in enumerate(GETBZOPDATE_DBIO_IDS):
        files[f"{dbio.DBIO_RESOURCE_ROOT}/{dbio.DBIO_FILENAME_PREFIX}{dbio_id}.xml"] = _synth_dbio_xml(f"TBL_{i}")
    return files


def test_extract_from_module_biz_recurses_into_all_dbio_refs():
    # 실물 biz 소스(MPCOM_GetBzopDate.c)의 DBIO 8개(VS004~VS011) 전부 도달하는지 검증.
    # 실물 XML 픽스처는 없어 합성 XML을 fake reader에 주입한다.
    reader = FakeReader(_getbzopdate_files())
    result = service.extract_from_module("biz", "PCOM", "MPCOM_GetBzopDate", reader)

    assert result.tables == [f"TBL_{i}" for i in range(8)]
    assert result.dbios == GETBZOPDATE_DBIO_IDS
    assert result.bizs == ["MPCOM_GetBzopDate"]  # 진입 모듈 자기 자신 포함(dbio의 self-inclusion과 동일 규칙)
    assert result.services == []


def test_extract_from_module_recursion_find_cycle_and_partial_success():
    svc_path = module_path("service", "PCSP", "SVC1")
    biz_path = module_path("biz", "NCOM", "BIZ_A")  # 재귀 중 발견 → resource_group 모름 → find로 찾아야 함

    svc_src = (
        'PFM_TRYNJ(pfmDlCall("BIZ_A", "BIZ_A", &in, &out));\n'
        'PFM_TRYNJ(pfmDbioSelect("PFO_ABC_DS001", &in, &out));\n'
        'PFM_TRYNJ(pfmDlCall("BIZ_MISSING", "BIZ_MISSING", &in, &out));\n'
    )
    biz_src = (
        # 순환 참조: SVC1을 다시 호출 → 이미 visited라 재방문 없이 skip돼야 함
        # (cycle 차단이 깨지면 SVC1↔BIZ_A가 무한 재귀에 빠져 이 테스트가 멈추거나 RecursionError로 실패)
        'PFM_TRYNJ(pfmDlCall("SVC1", "SVC1", &in, &out));\n'
        # 존재하지 않는 DBIO 참조 → nested 실패는 skip(부분성공)
        'PFM_TRYNJ(pfmDbioSelect("PFO_XYZ_DS002", &in, &out));\n'
    )

    files = {
        svc_path: svc_src,
        biz_path: biz_src,
        f"{dbio.DBIO_RESOURCE_ROOT}/{dbio.DBIO_FILENAME_PREFIX}PFO_ABC_DS001.xml": _synth_dbio_xml("SVC_TBL"),
        # PFO_XYZ_DS002.xml 없음(nested skip), BIZ_MISSING 소스도 없음(find 실패 → nested skip)
    }
    dirs = {COMPILE_ROOT: ["PCSP", "NCOM"]}  # find가 순회할 업무그룹 후보

    result = service.extract_from_module("service", "PCSP", "SVC1", FakeReader(files, dirs))

    assert result.tables == ["SVC_TBL"]
    assert result.dbios == ["PFO_ABC_DS001"]
    assert result.services == ["SVC1"]  # 진입 모듈 자기 자신
    assert result.bizs == ["BIZ_A"]     # BIZ_MISSING은 소스 조회 실패(skip)라 안 들어감


def test_extract_from_module_group_map_skips_find_for_hit():
    # group_map에 있는 참조는 find(COMPILE_ROOT listdir + 후보 순차 시도) 없이 바로 읽어야 한다.
    svc_path = module_path("service", "PCSP", "SVC1")
    biz_path = module_path("biz", "NCOM", "BIZ_A")

    files = {svc_path: 'PFM_TRYNJ(pfmDlCall("BIZ_A", "BIZ_A", &in, &out));\n', biz_path: ""}
    # dirs를 비워둠: find가 시도되면 COMPILE_ROOT listdir에서 SourceNotFound가 나 실패한다.
    reader = FakeReader(files, dirs={})
    group_map = {("biz", "BIZ_A"): "NCOM"}

    result = service.extract_from_module("service", "PCSP", "SVC1", reader, group_map=group_map)

    assert result.tables == []
    assert biz_path in reader.read_calls
    assert reader.listdir_calls == []  # find(순차 탐색)가 아예 시도되지 않았음


def test_extract_from_module_group_map_stale_entry_falls_back_to_find():
    # group_map이 틀린 그룹을 가리켜도 기존 순차 탐색(find)으로 정답을 찾아야 한다.
    svc_path = module_path("service", "PCSP", "SVC1")
    biz_path = module_path("biz", "NCOM", "BIZ_A")

    files = {svc_path: 'PFM_TRYNJ(pfmDlCall("BIZ_A", "BIZ_A", &in, &out));\n', biz_path: ""}
    reader = FakeReader(files, dirs={COMPILE_ROOT: ["PCSP", "NCOM"]})
    group_map = {("biz", "BIZ_A"): "PCSP"}  # 실제로는 NCOM 소속(잘못된 매핑)

    result = service.extract_from_module("service", "PCSP", "SVC1", reader, group_map=group_map)

    assert result.tables == []
    assert biz_path in reader.read_calls
    assert reader.listdir_calls == [COMPILE_ROOT]  # 매핑 실패 후 순차 탐색으로 폴백


def test_extract_from_module_loads_group_map_from_env_at_top_level(monkeypatch, tmp_path):
    # 최상위 호출은 group_map을 명시하지 않아도 env로 지정된 매핑 파일을 자동 로드해야 한다.
    svc_path = module_path("service", "PCSP", "SVC1")
    biz_path = module_path("biz", "NCOM", "BIZ_A")
    files = {svc_path: 'PFM_TRYNJ(pfmDlCall("BIZ_A", "BIZ_A", &in, &out));\n', biz_path: ""}
    reader = FakeReader(files, dirs={})  # find가 시도되면 실패하도록 비워둠

    map_file = tmp_path / "module_group_map.txt"
    map_file.write_text("BIZ_A\tNCOM\tbiz\n", encoding="utf-8")
    monkeypatch.setenv("NOGADA_MODULE_GROUP_MAP_PATH", str(map_file))

    result = service.extract_from_module("service", "PCSP", "SVC1", reader)

    assert result.tables == []
    assert biz_path in reader.read_calls
    assert reader.listdir_calls == []


def test_extract_from_module_batch_ref_recorded_not_recursed():
    # 실물 케이스: SRLGR96602A.c는 bat_code="BRLGRPRP0001" 리터럴(batch)과
    # pfmDlCall("MZPFM_BatchLinkCall", ...)(biz, 소스 없음) 둘 다 참조로 잡힌다.
    # batch는 소스를 찾으려 하지 않고 이름만 batches에 기록해야 한다.
    src = (COMPILE_FIXTURE_ROOT / "RLGR/src/serviceModule/SRLGR96602A/SRLGR96602A.c").read_text("utf-8")
    svc_path = module_path("service", "RLGR", "SRLGR96602A")
    reader = FakeReader({svc_path: src}, dirs={COMPILE_ROOT: ["RLGR"]})

    result = service.extract_from_module("service", "RLGR", "SRLGR96602A", reader)

    assert result.batches == ["BRLGRPRP0001"]
    assert result.services == ["SRLGR96602A"]  # 진입 모듈 자기 자신(biz 참조 MZPFM_BatchLinkCall은 소스 없어 skip)
    # batch ID로는 read/listdir를 전혀 시도하지 않아야 한다(소스를 들여다보지 않음).
    assert not any("BRLGRPRP0001" in p for p in reader.read_calls)
    assert not any("BRLGRPRP0001" in p for p in reader.listdir_calls)


def test_extract_from_module_excluded_ref_skipped_without_read():
    # 재귀 중 만나는 참조가 제외 목록에 있으면 소스를 읽지 않고 스킵돼야 한다.
    excluded_id = GETBZOPDATE_DBIO_IDS[0]
    reader = FakeReader(_getbzopdate_files())
    result = service.extract_from_module(
        "biz", "PCOM", "MPCOM_GetBzopDate", reader, excluded={excluded_id},
    )

    assert excluded_id not in result.dbios
    assert result.dbios == GETBZOPDATE_DBIO_IDS[1:]
    assert not any(excluded_id in p for p in reader.read_calls)


def test_excluded_ref_as_top_level_still_processed(monkeypatch, tmp_path):
    # 제외 목록에 있는 ID라도 최상위(dbio 라우터 엔트리)로 직접 요청하면 그대로 처리돼야 한다.
    excl_file = tmp_path / "excluded_refs.txt"
    excl_file.write_text("PFO_STCK_MA_DS200\n", encoding="utf-8")
    monkeypatch.setenv("NOGADA_EXCLUDED_REFS_PATH", str(excl_file))

    reader = FakeReader({DS200_PATH: DS200_XML})
    result = service.extract("dbio", None, "PFO_STCK_MA_DS200", reader)
    assert result.dbios == ["PFO_STCK_MA_DS200"]


def test_extract_from_module_top_level_not_found_propagates():
    # 최상위 진입 모듈 자체가 없으면(재귀 중 실패와 달리) 그대로 전파돼야 함(→ 라우터 404).
    with pytest.raises(SourceNotFound):
        service.extract_from_module("biz", "PCOM", "NO_SUCH_MODULE", FakeReader({}))


def test_extract_dispatches_dbio_to_leaf_without_recursion():
    reader = FakeReader({DS200_PATH: DS200_XML})
    result = service.extract("dbio", None, "PFO_STCK_MA_DS200", reader)
    assert result.dbios == ["PFO_STCK_MA_DS200"]


def test_extract_dispatches_non_dbio_to_module_recursion():
    reader = FakeReader(_getbzopdate_files())
    result = service.extract("biz", "PCOM", "MPCOM_GetBzopDate", reader)
    assert result.dbios == GETBZOPDATE_DBIO_IDS


def test_extract_filters_excluded_tables_from_result(monkeypatch, tmp_path):
    # excluded_tables.txt에 등록된 테이블은 최종 tables에서만 빠지고, 추출근거(dbios)는 그대로 남는다.
    excl_file = tmp_path / "excluded_tables.txt"
    excl_file.write_text("PFO_SPA_MA\n", encoding="utf-8")
    monkeypatch.setenv("NOGADA_EXCLUDED_TABLES_PATH", str(excl_file))

    reader = FakeReader({DS200_PATH: DS200_XML})
    result = service.extract("dbio", None, "PFO_STCK_MA_DS200", reader)

    assert "PFO_SPA_MA" not in result.tables
    assert "PFO_STCK_MA" in result.tables
    assert result.dbios == ["PFO_STCK_MA_DS200"]


def test_extract_no_excluded_tables_file_keeps_all_tables(monkeypatch, tmp_path):
    monkeypatch.setenv("NOGADA_EXCLUDED_TABLES_PATH", str(tmp_path / "absent.txt"))

    reader = FakeReader({DS200_PATH: DS200_XML})
    result = service.extract("dbio", None, "PFO_STCK_MA_DS200", reader)

    assert "PFO_SPA_MA" in result.tables


# ---- router ----

def test_dbio_extract_success():
    # DBIO는 리소스그룹 없이 2세그먼트 경로로 호출한다(정규 형태).
    _use_files({DS200_PATH: DS200_XML})
    resp = client.get("/table-extractor/dbio/PFO_STCK_MA_DS200")
    assert resp.status_code == 200
    body = resp.json()
    assert body["tables"] == sorted(
        ["PFO_STCK_MA", "TRU_STCK_ITMS_HT", "PFO_BRWN_STCK_MA", "PFO_SPA_MA", "PFO_SPA_ITMS_HT"]
    )
    assert body["dbios"] == ["PFO_STCK_MA_DS200"]


def test_dbio_extract_execsql_success():
    _use_files({EI901_PATH: EI901_XML})
    resp = client.get("/table-extractor/dbio/PFO_MNCM_CLCD_HT_EI901")
    assert resp.status_code == 200
    assert "PFO_MNCM_CLCD_HT" in resp.json()["tables"]


def test_dbio_extract_three_segment_still_works():
    # 하위호환: resource_group을 준 3세그먼트 경로도 DBIO에서 그대로 동작(값은 무시).
    _use_files({DS200_PATH: DS200_XML})
    resp = client.get("/table-extractor/dbio/PCSP/PFO_STCK_MA_DS200")
    assert resp.status_code == 200
    assert resp.json()["dbios"] == ["PFO_STCK_MA_DS200"]


def test_dbio_extract_file_not_found_returns_404():
    resp = client.get("/table-extractor/dbio/PFO_STCK_MA_DS200")
    assert resp.status_code == 404


def test_dbio_extract_unrecognized_id_pattern_returns_400():
    resp = client.get("/table-extractor/dbio/SOME_ID")
    assert resp.status_code == 400


def test_non_dbio_extract_success_recurses_via_router():
    _use_files(_getbzopdate_files())
    resp = client.get("/table-extractor/biz/PCOM/MPCOM_GetBzopDate")
    assert resp.status_code == 200
    body = resp.json()
    assert body["dbios"] == GETBZOPDATE_DBIO_IDS
    assert body["bizs"] == ["MPCOM_GetBzopDate"]
    assert body["services"] == []


def test_non_dbio_without_resource_group_returns_400():
    # DBIO와 달리 service/batch/biz는 최상위 진입 모듈의 업무그룹을 반드시 알아야 한다(2세그먼트 금지).
    resp = client.get("/table-extractor/biz/MPCOM_GetBzopDate")
    assert resp.status_code == 400


def test_non_dbio_top_level_file_not_found_returns_404():
    resp = client.get("/table-extractor/service/PCSP/SOME_ID")
    assert resp.status_code == 404


def test_invalid_prog_rejected():
    resp = client.get("/table-extractor/dbio/XXXX/SOME_ID")
    assert resp.status_code == 422


def test_invalid_id_type_rejected():
    resp = client.get("/table-extractor/bogus/PCSP/SOME_ID")
    assert resp.status_code == 422


def test_whitespace_only_id_rejected():
    resp = client.get("/table-extractor/dbio/%20")
    assert resp.status_code == 400


def test_route_is_get_without_body():
    resp = client.post("/table-extractor/dbio/PCSP/SOME_ID")
    assert resp.status_code == 405


# ---- POST /table-extractor/{module_type}/extract-batch (여러 ID 동시 추출) ----

def test_batch_extract_dbio_success_all():
    _use_files({DS200_PATH: DS200_XML, EI901_PATH: EI901_XML})
    resp = client.post("/table-extractor/dbio/extract-batch", json={
        "file_ids": ["PFO_STCK_MA_DS200", "PFO_MNCM_CLCD_HT_EI901"],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["succeeded"] == ["PFO_STCK_MA_DS200", "PFO_MNCM_CLCD_HT_EI901"]
    assert body["failed"] == []
    assert set(body["dbios"]) == {"PFO_STCK_MA_DS200", "PFO_MNCM_CLCD_HT_EI901"}
    assert "PFO_STCK_MA" in body["tables"]
    assert "PFO_MNCM_CLCD_HT" in body["tables"]


def test_batch_extract_partial_failure_returns_200_with_failed_list():
    _use_files({DS200_PATH: DS200_XML})
    resp = client.post("/table-extractor/dbio/extract-batch", json={
        "file_ids": ["PFO_STCK_MA_DS200", "PFO_MISSING_DS999"],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["succeeded"] == ["PFO_STCK_MA_DS200"]
    assert len(body["failed"]) == 1
    assert body["failed"][0]["file_id"] == "PFO_MISSING_DS999"
    assert "404" in body["failed"][0]["error"]
    assert "PFO_STCK_MA" in body["tables"]


def test_batch_extract_all_fail_still_returns_200():
    resp = client.post("/table-extractor/dbio/extract-batch", json={
        "file_ids": ["PFO_MISSING_DS999", "PFO_MISSING_DS998"],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["succeeded"] == []
    assert len(body["failed"]) == 2
    assert body["tables"] == []


def test_batch_extract_empty_list_returns_400():
    resp = client.post("/table-extractor/dbio/extract-batch", json={"file_ids": []})
    assert resp.status_code == 400


def test_batch_extract_whitespace_only_ids_rejected():
    resp = client.post("/table-extractor/dbio/extract-batch", json={"file_ids": ["  ", ""]})
    assert resp.status_code == 400


def test_batch_extract_exceeds_max_batch_size_returns_400():
    resp = client.post("/table-extractor/dbio/extract-batch", json={
        "file_ids": [f"ID_{i}" for i in range(51)],
    })
    assert resp.status_code == 400


def test_batch_extract_non_dbio_missing_resource_group_returns_400():
    resp = client.post("/table-extractor/service/extract-batch", json={
        "file_ids": ["SOME_ID"],
    })
    assert resp.status_code == 400


def test_batch_extract_duplicate_ids_deduped():
    _use_files({DS200_PATH: DS200_XML})
    resp = client.post("/table-extractor/dbio/extract-batch", json={
        "file_ids": ["PFO_STCK_MA_DS200", "PFO_STCK_MA_DS200", " PFO_STCK_MA_DS200 "],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["succeeded"] == ["PFO_STCK_MA_DS200"]
    assert body["dbios"] == ["PFO_STCK_MA_DS200"]


def test_batch_extract_dbios_cross_item_dedup_preserves_order():
    # SVC_A -> (공유 DBIO, A전용 DBIO), SVC_B -> (같은 공유 DBIO, B전용 DBIO).
    # 각 항목이 독립된 visited로 top-level 처리되므로 공유 DBIO가 두 번 나올 수 있는데,
    # extract_batch가 최초 등장 순서를 유지하며 dedupe해야 한다.
    svc_a_path = module_path("service", "PCSP", "SVC_A")
    svc_b_path = module_path("service", "PCSP", "SVC_B")
    svc_a_src = (
        'PFM_TRYNJ(pfmDbioSelect("PFO_SHARED_DS001", &in, &out));\n'
        'PFM_TRYNJ(pfmDbioSelect("PFO_ONLY_A_DS002", &in, &out));\n'
    )
    svc_b_src = (
        'PFM_TRYNJ(pfmDbioSelect("PFO_SHARED_DS001", &in, &out));\n'
        'PFM_TRYNJ(pfmDbioSelect("PFO_ONLY_B_DS003", &in, &out));\n'
    )
    files = {
        svc_a_path: svc_a_src,
        svc_b_path: svc_b_src,
        f"{dbio.DBIO_RESOURCE_ROOT}/{dbio.DBIO_FILENAME_PREFIX}PFO_SHARED_DS001.xml": _synth_dbio_xml("SHARED_TBL"),
        f"{dbio.DBIO_RESOURCE_ROOT}/{dbio.DBIO_FILENAME_PREFIX}PFO_ONLY_A_DS002.xml": _synth_dbio_xml("A_TBL"),
        f"{dbio.DBIO_RESOURCE_ROOT}/{dbio.DBIO_FILENAME_PREFIX}PFO_ONLY_B_DS003.xml": _synth_dbio_xml("B_TBL"),
    }
    _use_files(files)

    resp = client.post("/table-extractor/service/extract-batch", json={
        "resource_group": "PCSP",
        "file_ids": ["SVC_A", "SVC_B"],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["succeeded"] == ["SVC_A", "SVC_B"]
    assert body["dbios"] == ["PFO_SHARED_DS001", "PFO_ONLY_A_DS002", "PFO_ONLY_B_DS003"]
    assert set(body["tables"]) == {"SHARED_TBL", "A_TBL", "B_TBL"}


def test_batch_extract_excluded_tables_filter_still_applies_per_item(monkeypatch, tmp_path):
    excl_file = tmp_path / "excluded_tables.txt"
    excl_file.write_text("PFO_SPA_MA\n", encoding="utf-8")
    monkeypatch.setenv("NOGADA_EXCLUDED_TABLES_PATH", str(excl_file))
    _use_files({DS200_PATH: DS200_XML})

    resp = client.post("/table-extractor/dbio/extract-batch", json={
        "file_ids": ["PFO_STCK_MA_DS200"],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "PFO_SPA_MA" not in body["tables"]
    assert "PFO_STCK_MA" in body["tables"]


# ---- POST /table-extractor/pks (PK 컬럼 조회) ----

PK_ROWS = [
    {"table_id": "PFO_STCK_MA", "pk_column": "mncm_code"},
    {"table_id": "PFO_STCK_MA", "pk_column": "fund_code"},
    {"table_id": "PFO_STCK_MA", "pk_column": "proc_date"},
    {"table_id": "PFO_STCK_MA", "pk_column": "itms_code"},
    {"table_id": "PFO_FUND_BS", "pk_column": "mncm_code"},
    {"table_id": "PFO_FUND_BS", "pk_column": "fund_code"},
]


class FakeDb:
    def __init__(self, rows: list[Row]):
        self._rows = rows

    def query(self, sql: str, params: Params = None) -> list[Row]:
        wanted = set((params or {}).get("tables", []))
        return [r for r in self._rows if r["table_id"] in wanted]


class BrokenDb:
    def query(self, sql: str, params: Params = None) -> list[Row]:
        raise DbError("접속 실패")


def _use_db(db) -> None:
    app.dependency_overrides[default_db] = lambda: db


def test_pks_success_groups_by_table():
    _use_db(FakeDb(PK_ROWS))
    resp = client.post("/table-extractor/pks", json={"tables": ["PFO_STCK_MA", "PFO_FUND_BS"]})
    assert resp.status_code == 200
    assert resp.json()["pks"] == {
        "PFO_STCK_MA": ["mncm_code", "fund_code", "proc_date", "itms_code"],
        "PFO_FUND_BS": ["mncm_code", "fund_code"],
    }


def test_pks_unknown_table_included_as_empty():
    _use_db(FakeDb(PK_ROWS))
    resp = client.post("/table-extractor/pks", json={"tables": ["PFO_STCK_MA", "ZZZ"]})
    assert resp.status_code == 200
    assert resp.json()["pks"]["ZZZ"] == []


def test_pks_empty_list_returns_empty_map():
    _use_db(FakeDb(PK_ROWS))
    resp = client.post("/table-extractor/pks", json={"tables": []})
    assert resp.status_code == 200
    assert resp.json()["pks"] == {}


def test_pks_db_error_returns_503():
    _use_db(BrokenDb())
    resp = client.post("/table-extractor/pks", json={"tables": ["PFO_STCK_MA"]})
    assert resp.status_code == 503


def test_pks_missing_body_field_rejected():
    resp = client.post("/table-extractor/pks", json={})
    assert resp.status_code == 422


# ---- POST /table-extractor/migrate-sql (DELETE/INSERT 생성) ----

def test_migrate_sql_generates_delete_insert():
    _use_db(FakeDb(PK_ROWS))
    resp = client.post("/table-extractor/migrate-sql", json={
        "tables": ["PFO_STCK_MA"],
        "from_link": "SRC",
        "to_link": "TGT",
        "keys": {
            "mncm_code": {"op": "eq", "value": "M1"},
            "fund_code": {"op": "eq", "value": "F1"},
            "proc_date": {"op": "eq", "value": "20250101"},
        },
    })
    assert resp.status_code == 200
    sql = resp.json()["sql"]
    assert "DELETE FROM PFO_STCK_MA@TGT" in sql
    assert "INSERT INTO PFO_STCK_MA@TGT" in sql
    assert "SELECT * FROM PFO_STCK_MA@SRC" in sql
    assert "mncm_code = 'M1'" in sql
    assert resp.json()["generated"] == ["PFO_STCK_MA"]
    # 접미사 그룹: PFO_STCK_MA → _MA 박스
    groups = resp.json()["groups"]
    assert [g["key"] for g in groups] == ["_MA"]
    assert groups[0]["tables"] == ["PFO_STCK_MA"]


def test_migrate_sql_lowercase_table_normalized():
    _use_db(FakeDb(PK_ROWS))
    resp = client.post("/table-extractor/migrate-sql", json={
        "tables": ["pfo_stck_ma"],
        "keys": {"mncm_code": {"op": "eq", "value": "M1"}},
    })
    assert resp.status_code == 200
    # 미입력 컬럼은 제외되고 mncm_code만 조건에 (테이블명은 대문자 정규화)
    assert "DELETE FROM PFO_STCK_MA" in resp.json()["sql"]


def test_migrate_sql_db_error_returns_503():
    _use_db(BrokenDb())
    resp = client.post("/table-extractor/migrate-sql", json={
        "tables": ["PFO_STCK_MA"], "keys": {"mncm_code": {"value": "M1"}},
    })
    assert resp.status_code == 503


# ---- GET/POST /table-extractor/excluded-tables, /excluded-refs (설정 팝업: 조회/저장) ----

@pytest.fixture(autouse=True)
def _excluded_tables_tmp_path(monkeypatch, tmp_path):
    # 기본 경로(config/excluded_tables.txt, config/excluded_refs.txt)를 건드리지 않도록
    # 매 테스트를 tmp_path로 격리한다.
    monkeypatch.setenv("NOGADA_EXCLUDED_TABLES_PATH", str(tmp_path / "excluded_tables.txt"))
    monkeypatch.setenv("NOGADA_EXCLUDED_REFS_PATH", str(tmp_path / "excluded_refs.txt"))


def test_get_excluded_tables_empty_when_unset():
    resp = client.get("/table-extractor/excluded-tables")
    assert resp.status_code == 200
    assert resp.json()["tables"] == []


def test_post_excluded_tables_saves_and_returns_normalized():
    resp = client.post("/table-extractor/excluded-tables", json={"tables": ["pfo_a", "PFO_B", "pfo_a"]})
    assert resp.status_code == 200
    assert resp.json()["tables"] == ["PFO_A", "PFO_B"]


def test_get_excluded_tables_reflects_previous_save():
    client.post("/table-extractor/excluded-tables", json={"tables": ["FOO", "BAR"]})
    resp = client.get("/table-extractor/excluded-tables")
    assert resp.status_code == 200
    assert resp.json()["tables"] == ["BAR", "FOO"]


def test_post_excluded_tables_empty_list_clears_saved():
    client.post("/table-extractor/excluded-tables", json={"tables": ["FOO"]})
    resp = client.post("/table-extractor/excluded-tables", json={"tables": []})
    assert resp.status_code == 200
    assert resp.json()["tables"] == []
    assert client.get("/table-extractor/excluded-tables").json()["tables"] == []


def test_post_excluded_tables_missing_body_field_rejected():
    resp = client.post("/table-extractor/excluded-tables", json={})
    assert resp.status_code == 422


# ---- GET/POST /table-extractor/excluded-refs (설정 팝업: 모듈 예외처리 조회/저장) ----

def test_get_excluded_refs_empty_when_unset():
    resp = client.get("/table-extractor/excluded-refs")
    assert resp.status_code == 200
    assert resp.json()["ids"] == []


def test_post_excluded_refs_saves_and_preserves_case():
    # 테이블명과 달리 ID는 대문자로 정규화하지 않는다(재귀 매칭이 대소문자 구분).
    resp = client.post("/table-extractor/excluded-refs", json={"ids": ["MZCOM_DeadBiz", "PFO_LEGACY_MA_DS999"]})
    assert resp.status_code == 200
    assert resp.json()["ids"] == ["MZCOM_DeadBiz", "PFO_LEGACY_MA_DS999"]


def test_get_excluded_refs_reflects_previous_save():
    client.post("/table-extractor/excluded-refs", json={"ids": ["FooId", "BarId"]})
    resp = client.get("/table-extractor/excluded-refs")
    assert resp.status_code == 200
    assert resp.json()["ids"] == ["BarId", "FooId"]


def test_post_excluded_refs_empty_list_clears_saved():
    client.post("/table-extractor/excluded-refs", json={"ids": ["FooId"]})
    resp = client.post("/table-extractor/excluded-refs", json={"ids": []})
    assert resp.status_code == 200
    assert resp.json()["ids"] == []
    assert client.get("/table-extractor/excluded-refs").json()["ids"] == []


def test_post_excluded_refs_missing_body_field_rejected():
    resp = client.post("/table-extractor/excluded-refs", json={})
    assert resp.status_code == 422
