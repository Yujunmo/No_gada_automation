"""COMPILE_ROOT 전체를 훑어 config/module_group_map.txt를 재생성한다.

table_extractor의 재귀 추출이 service/biz 참조를 만날 때마다 업무그룹을 몰라 최대
30회까지 순차 탐색(find 폴백)하는 비용을 줄이기 위한 사전 매핑을 만든다. 요청 경로가
아니라 이 스크립트를 통해 오프라인으로 실행한다 — 업무그룹마다 디렉터리를 통째로
listdir하므로 무겁다.

지금은 수동 실행(`python scripts/build_module_group_map.py`). 주기 자동화(cron 등)는
후속 과제 — 이 스크립트 자체는 몇 번을 반복 실행해도 항상 최신 상태로 덮어쓰므로,
나중에 cron이 이 스크립트를 호출하기만 하면 된다.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.common.io.sftp import default_reader
from app.common.proframe import module_source


def main() -> None:
    gen = default_reader()
    reader = next(gen)
    try:
        group_map = module_source.build_group_map(reader)
    finally:
        gen.close()

    module_source.write_group_map(group_map, module_source.DEFAULT_GROUP_MAP_PATH)
    print(f"{len(group_map)}개 항목 기록: {module_source.DEFAULT_GROUP_MAP_PATH}")


if __name__ == "__main__":
    main()
