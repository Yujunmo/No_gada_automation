"""ProFrame ID 체계 공용 타입.

id_type(DBIO/Service/Batch/Biz)·prog(업무그룹)는 table_extractor에서 먼저 쓰이지만
ProFrame ID 자체의 분류 체계라 다른 툴(예: 향후 Migration Builder)에서도 재사용될 값이다.
"""
from __future__ import annotations

from typing import Literal

# ID 타입 4종(DBIO/Service/Batch/Biz) — 원본 소스가 있는 계층 구분.
IdType = Literal["dbio", "service", "batch", "biz"]
# 업무그룹(리소스 그룹) 7종 — 원격 디렉토리 최상위 분류.
Prog = Literal["PCSP", "PCSH", "NCOM", "NCSP", "PCOM", "PPFR", "RLGR"]
