"""ProFrame 도메인 지식 계층 (io/ 위에 얹힘).

패키지 경계에서 자주 쓰이는 타입/상수는 types.py에서 재수출해
`from app.common.proframe import Module_Type` 형태를 지원한다
(파일이 아니라 패키지가 인터페이스). dbio/module_source/db_schema는
동작 단위라 각 모듈에서 직접 import.
"""
from __future__ import annotations

from app.common.proframe.types import (
    PROFRAME_ROOT,
    Module_Type,
    ResourceGroup,
)

__all__ = ["PROFRAME_ROOT", "Module_Type", "ResourceGroup"]
