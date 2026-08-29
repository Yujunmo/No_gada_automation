from __future__ import annotations

import pytest

from app.common.proframe.module_source import (
    build_group_map,
    load_group_map,
    module_path,
    parse_module_path,
    read_module_source,
    write_group_map,
)
from app.common.io.sftp import SourceNotFound, SourceReader

COMPILE_ROOT = "/truap01dap1/proframe/proframe5.0/compile"


class FakeReader:
    """SourceReader Protocol을 만족하는 인메모리 가짜(read + listdir + 호출 기록)."""

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


def test_fake_satisfies_protocol():
    assert isinstance(FakeReader({}), SourceReader)


def test_module_path_service_nests_under_own_id_dir():
    path = module_path("service", "PCSP", "SPCSP53619C")
    assert path == (
        "/truap01dap1/proframe/proframe5.0/compile/PCSP/src/serviceModule/SPCSP53619C/SPCSP53619C.c"
    )


def test_module_path_batch():
    path = module_path("batch", "RLGR", "BRLGRPRP0001")
    assert path == "/truap01dap1/proframe/proframe5.0/compile/RLGR/src/batch/BRLGRPRP0001.c"


def test_module_path_biz():
    path = module_path("biz", "PCOM", "MPCOM_GetBzopDate")
    assert path == "/truap01dap1/proframe/proframe5.0/compile/PCOM/src/module/MPCOM_GetBzopDate.c"


@pytest.mark.parametrize(
    "module_type, resource_group, file_id",
    [
        ("service", "PCSP", "SPCSP53619C"),
        ("batch", "RLGR", "BRLGRPRP0001"),
        ("biz", "PCOM", "MPCOM_GetBzopDate"),
    ],
)
def test_parse_module_path_round_trips_with_module_path(module_type, resource_group, file_id):
    path = module_path(module_type, resource_group, file_id)
    assert parse_module_path(path) == (module_type, resource_group, file_id)


def test_parse_module_path_rejects_path_outside_convention():
    assert parse_module_path("/truap01dap1/proframe/proframe5.0/release/dbio/xml/pfmDbioFOO.xml") is None
    assert parse_module_path("/some/unrelated/path.c") is None


def test_read_with_resource_group_reads_directly():
    path = module_path("biz", "PCOM", "MPCOM_GetBzopDate")
    reader = FakeReader({path: "int main() {}"})
    assert read_module_source("biz", "MPCOM_GetBzopDate", reader, resource_group="PCOM") == "int main() {}"


def test_read_without_resource_group_finds_across_groups():
    path = module_path("biz", "PCOM", "MPCOM_GetBzopDate")
    reader = FakeReader(
        files={path: "int main() {}"},
        dirs={"/truap01dap1/proframe/proframe5.0/compile": ["PCSP", "PCOM", "RLGR"]},
    )
    assert read_module_source("biz", "MPCOM_GetBzopDate", reader) == "int main() {}"


def test_read_without_resource_group_not_found_raises():
    reader = FakeReader(
        files={},
        dirs={"/truap01dap1/proframe/proframe5.0/compile": ["PCSP", "PCOM"]},
    )
    with pytest.raises(SourceNotFound):
        read_module_source("biz", "MPCOM_NoSuchModule", reader)


# --- group_map: build/load/write + read_module_source 가속 ---


def test_build_group_map_walks_groups_and_module_types():
    reader = FakeReader(
        files={},
        dirs={
            COMPILE_ROOT: ["PCSP", "PCOM"],
            f"{COMPILE_ROOT}/PCSP/src/serviceModule": ["SPCSP53619C"],
            f"{COMPILE_ROOT}/PCSP/src/module": ["MPCSP_Foo.c"],
            f"{COMPILE_ROOT}/PCOM/src/module": ["MPCOM_GetBzopDate.c"],
            # PCOM/src/serviceModule 없음 → SourceNotFound → skip
        },
    )
    group_map = build_group_map(reader)
    assert group_map == {
        ("service", "SPCSP53619C"): "PCSP",
        ("biz", "MPCSP_Foo"): "PCSP",
        ("biz", "MPCOM_GetBzopDate"): "PCOM",
    }


def test_build_group_map_skips_hidden_entries():
    # 실사용 중 발견: 로컬 macOS 픽스처 디렉터리에 .DS_Store가 섞여 들어와 가짜 ID로 잡혔었다.
    reader = FakeReader(
        files={},
        dirs={
            COMPILE_ROOT: ["PCSP"],
            f"{COMPILE_ROOT}/PCSP/src/serviceModule": [".DS_Store", "SPCSP53619C"],
            f"{COMPILE_ROOT}/PCSP/src/module": [".DS_Store"],
        },
    )
    group_map = build_group_map(reader)
    assert group_map == {("service", "SPCSP53619C"): "PCSP"}


def test_build_group_map_first_group_wins_on_duplicate():
    reader = FakeReader(
        files={},
        dirs={
            COMPILE_ROOT: ["PCSP", "PCOM"],
            f"{COMPILE_ROOT}/PCSP/src/module": ["MDUP_Id.c"],
            f"{COMPILE_ROOT}/PCOM/src/module": ["MDUP_Id.c"],
        },
    )
    group_map = build_group_map(reader)
    assert group_map[("biz", "MDUP_Id")] == "PCSP"


def test_load_group_map_missing_file_returns_empty():
    assert load_group_map("/no/such/path/module_group_map.txt") == {}


def test_write_then_load_group_map_roundtrip(tmp_path):
    path = tmp_path / "module_group_map.txt"
    group_map = {("service", "SPCSP53619C"): "PCSP", ("biz", "MPCOM_GetBzopDate"): "PCOM"}
    write_group_map(group_map, str(path))
    assert load_group_map(str(path)) == group_map


def test_write_then_load_group_map_follows_configured_encoding(monkeypatch, tmp_path):
    # NOGADA_SOURCE_ENCODING(회사 반입 시 비UTF-8로 전환)을 write/load 양쪽 다 따라야 한다.
    path = tmp_path / "module_group_map.txt"
    monkeypatch.setenv("NOGADA_SOURCE_ENCODING", "cp949")
    group_map = {("biz", "한글_ID"): "PCOM"}
    write_group_map(group_map, str(path))
    assert path.read_bytes().decode("cp949").count("한글_ID") == 1
    assert load_group_map(str(path)) == group_map


def test_load_group_map_ignores_comments_and_blank_lines(tmp_path):
    path = tmp_path / "module_group_map.txt"
    path.write_text(
        "# 주석\n"
        "\n"
        "MPCOM_GetBzopDate\tPCOM\tbiz  # 줄 끝 주석\n"
        "SPCSP53619C\tPCSP\tservice\n"
    )
    assert load_group_map(str(path)) == {
        ("biz", "MPCOM_GetBzopDate"): "PCOM",
        ("service", "SPCSP53619C"): "PCSP",
    }


def test_read_module_source_uses_group_map_without_sequential_find():
    path = module_path("biz", "PCOM", "MPCOM_GetBzopDate")
    reader = FakeReader(
        files={path: "int main() {}"},
        dirs={COMPILE_ROOT: ["PCSP", "PCOM", "RLGR"]},
    )
    group_map = {("biz", "MPCOM_GetBzopDate"): "PCOM"}
    result = read_module_source("biz", "MPCOM_GetBzopDate", reader, group_map=group_map)
    assert result == "int main() {}"
    assert reader.read_calls == [path]
    assert reader.listdir_calls == []  # 순차 탐색(COMPILE_ROOT 나열)이 아예 안 일어남


def test_read_module_source_falls_back_when_group_map_stale():
    path = module_path("biz", "PCOM", "MPCOM_GetBzopDate")
    reader = FakeReader(
        files={path: "int main() {}"},
        dirs={COMPILE_ROOT: ["PCSP", "PCOM", "RLGR"]},
    )
    # 매핑이 틀린 그룹(RLGR)을 가리켜도 순차 탐색으로 정답(PCOM)을 찾아야 한다.
    group_map = {("biz", "MPCOM_GetBzopDate"): "RLGR"}
    result = read_module_source("biz", "MPCOM_GetBzopDate", reader, group_map=group_map)
    assert result == "int main() {}"
    assert reader.listdir_calls == [COMPILE_ROOT]


def test_read_module_source_without_group_map_behaves_as_before():
    path = module_path("biz", "PCOM", "MPCOM_GetBzopDate")
    reader = FakeReader(
        files={path: "int main() {}"},
        dirs={COMPILE_ROOT: ["PCSP", "PCOM", "RLGR"]},
    )
    assert read_module_source("biz", "MPCOM_GetBzopDate", reader) == "int main() {}"
    assert reader.listdir_calls == [COMPILE_ROOT]
