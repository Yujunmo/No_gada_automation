"""service/batch/biz 모듈 C 소스 위치 규칙 + 조회 (dbio.py의 자매).

DBIO는 release/dbio/xml에 평면 배치라 경로 1회 조합으로 끝나지만, service/batch/biz는
compile/<업무그룹>/src/{serviceModule/<ID>/<ID>.c | batch/<ID>.c | module/<ID>.c}처럼
경로에 업무그룹이 들어간다. 최상위 진입 모듈은 호출부(프론트)가 업무그룹을 알고 있어 바로
조합하면 되지만, 재귀 중 새로 발견되는 참조는 어느 업무그룹 소속인지 알 수 없으므로
COMPILE_ROOT를 나열(listdir)해 후보 경로를 순서대로 read 시도하는 "find" 폴백이 필요하다.

"""
from __future__ import annotations

import os

from app.common.io.sftp import SourceNotFound, SourceReader
from app.common.proframe.types import PROFRAME_ROOT, Module_Type

COMPILE_ROOT = f"{PROFRAME_ROOT}/compile"
MODULE_SUBDIR = {"service": "serviceModule", "batch": "batch", "biz": "module"}

DEFAULT_GROUP_MAP_PATH = "config/module_group_map.txt"


def _relpath(module_type: Module_Type, file_id: str) -> str:
    sub = MODULE_SUBDIR[module_type]
    if module_type == "service":
        return f"{sub}/{file_id}/{file_id}.c"
    return f"{sub}/{file_id}.c"


def module_path(module_type: Module_Type, resource_group: str, file_id: str) -> str:
    """업무그룹을 알 때(최상위 진입 모듈) 경로를 직접 조합한다."""
    return f"{COMPILE_ROOT}/{resource_group}/src/{_relpath(module_type, file_id)}"


def read_module_source(
    module_type: Module_Type,
    file_id: str,
    reader: SourceReader,
    resource_group: str | None = None,
    group_map: dict[tuple[str, str], str] | None = None,
) -> str:
    """module_type/ID (+업무그룹) → 원격 C 소스 조회.

    resource_group이 있으면(최상위) module_path로 바로 read.
    없으면(재귀 중 발견된 참조) 우선 group_map(ID→업무그룹 사전 매핑)을 참고해 바로
    read 시도하고, 매핑에 없거나 매핑이 틀렸으면(SourceNotFound) COMPILE_ROOT를
    listdir해 각 업무그룹 후보 경로를 순서대로 read 시도(find), 첫 성공을 반환.
    전부 실패하면 SourceNotFound.
    """
    # resource_group이 있으면(최상위) module_path로 바로 read.
    if resource_group is not None:
        return reader.read(module_path(module_type, resource_group, file_id))
    
    # resource_group이 없으면(재귀 중 발견된 참조) 우선 group_map(ID→업무그룹 사전 매핑)을 참고해 바로 read 시도
    if group_map:
        cached_group = group_map.get((module_type, file_id))
        if cached_group is not None:
            try:
                return reader.read(module_path(module_type, cached_group, file_id))
            except SourceNotFound:
                pass  # 매핑이 stale함 → 아래 순차 탐색으로 폴백

    # config/module_group_map.txt에서 매핑을 못 찾은 경우(또는 매핑이 stale함) → COMPILE_ROOT를 나열해 순차 탐색(find)
    rel = _relpath(module_type, file_id)
    groups = reader.listdir(COMPILE_ROOT)
    for group in groups:
        try:
            return reader.read(f"{COMPILE_ROOT}/{group}/src/{rel}")
        except SourceNotFound:
            continue
    raise SourceNotFound(
        f"모듈 소스 없음(업무그룹 {len(groups)}개 탐색 실패): module_type={module_type} file_id={file_id}"
    )


def build_group_map(reader: SourceReader) -> dict[tuple[str, str], str]:
    """COMPILE_ROOT 전체를 나열해 (module_type, file_id) -> resource_group 매핑을 새로 만든다.

    요청 경로가 아니라 오프라인 배치(scripts/build_module_group_map.py)에서만 호출한다 —
    업무그룹마다 service/biz 디렉터리를 통째로 listdir하므로, 파일이 많은 환경에서는
    read_module_source의 개별 find 폴백(경로 하나 열어보기)보다 훨씬 무겁다.
    같은 ID가 여러 그룹에 있으면(정상적으론 없어야 함) COMPILE_ROOT 나열 순서상 먼저
    발견된 그룹을 채택 — 기존 find 폴백의 "첫 성공 채택" 우선순위와 동일하게 맞춘다.
    """
    groups = reader.listdir(COMPILE_ROOT)
    group_map: dict[tuple[str, str], str] = {}
    for module_type in ("service", "biz"):
        sub = MODULE_SUBDIR[module_type]
        for group in groups:
            try:
                entries = reader.listdir(f"{COMPILE_ROOT}/{group}/src/{sub}")
            except SourceNotFound:
                continue
            for name in entries:
                if name.startswith("."):
                    continue  # .DS_Store 등 파일시스템 메타파일 — 실제 ProFrame ID는 점으로 시작하지 않음
                file_id = name[:-2] if name.endswith(".c") else name
                group_map.setdefault((module_type, file_id), group)
    return group_map


def load_group_map(path: str | None = None) -> dict[tuple[str, str], str]:
    """설정 파일에서 (module_type, file_id) -> resource_group 매핑을 읽는다.

    한 줄에 `ID<TAB>GROUP<TAB>MODULE_TYPE`(가독성 위해 ID를 맨 앞에 둠 — 내부 dict 키
    순서 (module_type, file_id)와는 다름, 조회 편의상 그대로 유지), `#` 뒤는 주석, 빈
    줄은 무시. 파일이 없으면 빈 dict(선택적 가속 기능이라 미설정 시 read_module_source가
    기존 순차 탐색으로 동작하는 게 안전한 기본값) — load_excluded_refs와 동일한 관용구.
    """
    path = path if path is not None else os.environ.get("NOGADA_MODULE_GROUP_MAP_PATH", DEFAULT_GROUP_MAP_PATH)
    if not os.path.isfile(path):
        return {}

    group_map: dict[tuple[str, str], str] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            file_id, group, module_type = parts
            group_map[(module_type, file_id)] = group
    return group_map


def write_group_map(group_map: dict[tuple[str, str], str], path: str) -> None:
    """group_map을 load_group_map이 읽을 수 있는 포맷으로 파일에 쓴다(빌드 스크립트 전용).

    사람이 diff를 보기 쉽도록 ID 기준으로 정렬해서 쓴다(같은 ID가 타입만 다르게
    여러 줄 나오는 경우도 붙어 보이도록 (file_id, module_type) 순).
    """
    lines = [
        "# ID → 업무그룹 매핑 (find 폴백 가속용, 없어도 동작에는 문제 없음 — 순차 탐색으로 폴백)",
        "#",
        "# 한 줄에 `ID\tGROUP\tMODULE_TYPE`. `#` 뒤는 주석. 빈 줄 무시.",
        "# 사람이 직접 편집하지 말 것 — scripts/build_module_group_map.py로 재생성.",
        "# 로더: app/common/proframe/module_source.py::load_group_map",
        "# 경로를 바꾸려면 NOGADA_MODULE_GROUP_MAP_PATH 환경변수 사용.",
        "",
    ]
    for (module_type, file_id), group in sorted(group_map.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        lines.append(f"{file_id}\t{group}\t{module_type}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
