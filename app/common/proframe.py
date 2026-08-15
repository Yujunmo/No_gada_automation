"""ProFrame ID 체계 공용 타입 + 환경 공용 경로.

module_type(DBIO/Service/Batch/Biz)·resource_group(업무그룹)는 table_extractor에서 먼저 쓰이지만
ProFrame ID 자체의 분류 체계라 다른 툴(예: 향후 Migration Builder)에서도 재사용될 값이다.
"""
from __future__ import annotations

from typing import Literal

# ID 타입 4종(DBIO/Service/Batch/Biz) — 원본 소스가 있는 계층 구분.
Module_Type = Literal["dbio", "service", "batch", "biz"]
# 업무그룹(리소스 그룹) 7종 — 원격 디렉토리 최상위 분류.
ResourceGroup = Literal["PCSP", "PCSH", "NCOM", "NCSP", "PCOM", "PPFR", "RLGR"]

# 서버/버전 고정 ProFrame 설치 루트. dbio.py(release/dbio/xml)·module_src.py(compile)가
# 각자의 하위 루트를 여기서 조합한다 — 서버 이전/버전 변경 시 한 곳만 고치면 되도록.
PROFRAME_ROOT = "/src/truap01dap1/proframe/proframe5.0"
