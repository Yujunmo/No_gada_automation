"""service/batch/biz 모듈 C 소스 위치 규칙 + 조회 (dbio.py의 자매).

DBIO는 release/dbio/xml에 평면 배치라 경로 1회 조합으로 끝나지만, service/batch/biz는
compile/<업무그룹>/src/{serviceModule/<ID>/<ID>.c | batch/<ID>.c | module/<ID>.c}처럼
경로에 업무그룹이 들어간다. 최상위 진입 모듈은 호출부(프론트)가 업무그룹을 알고 있어 바로
조합하면 되지만, 재귀 중 새로 발견되는 참조는 어느 업무그룹 소속인지 알 수 없으므로
COMPILE_ROOT를 나열(listdir)해 후보 경로를 순서대로 read 시도하는 "find" 폴백이 필요하다.
"""
from __future__ import annotations

from app.common.proframe import PROFRAME_ROOT, Module_Type
from app.common.source import SourceNotFound, SourceReader

COMPILE_ROOT = f"{PROFRAME_ROOT}/compile"
MODULE_SUBDIR = {"service": "serviceModule", "batch": "batch", "biz": "module"}


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
) -> str:
    """module_type/ID (+업무그룹) → 원격 C 소스 조회.

    resource_group이 있으면(최상위) module_path로 바로 read.
    없으면(재귀 중 발견된 참조) COMPILE_ROOT를 listdir해 각 업무그룹 후보 경로를
    순서대로 read 시도, 첫 성공을 반환(find). 전부 실패하면 SourceNotFound.
    """
    if resource_group is not None:
        return reader.read(module_path(module_type, resource_group, file_id))

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
