"""
plan.md의 회귀 케이스 20개.

Step 1 스켈레톤 상태에선 일부(특히 CTE alias / 인라인 뷰 alias / 다중 문장 관련)가
실패한다. Step 2에서 스코프 분석 로직을 붙이면 전 케이스 통과가 목표.
"""
from __future__ import annotations

import pytest

from app.extractor import ExtractionError, extract_tables


@pytest.mark.parametrize(
    "sql, expected",
    [
        # 1. alias 제외
        ("SELECT * FROM EMP e JOIN DEPT d ON e.id = d.id", ["DEPT", "EMP"]),
        # 2. CTE alias 제외, 본문 테이블 포함
        (
            "WITH t AS (SELECT * FROM EMP) SELECT * FROM t JOIN DEPT ON t.id = DEPT.id",
            ["DEPT", "EMP"],
        ),
        # 3. 인라인 뷰 alias 제외
        ("SELECT * FROM (SELECT id FROM EMP) x", ["EMP"]),
        # 4. MERGE 양쪽
        (
            "MERGE INTO target t USING source s ON (t.id=s.id) "
            "WHEN MATCHED THEN UPDATE SET t.v=s.v",
            ["SOURCE", "TARGET"],
        ),
        # 5. MERGE USING 서브쿼리
        (
            "MERGE INTO target USING (SELECT * FROM src) s ON (target.id=s.id) "
            "WHEN MATCHED THEN UPDATE SET v=s.v",
            ["SRC", "TARGET"],
        ),
        # 6. multi-table INSERT
        (
            "INSERT ALL INTO t1 VALUES (1) INTO t2 VALUES (2) SELECT * FROM src",
            ["SRC", "T1", "T2"],
        ),
        # 7. UPDATE + 상관 서브쿼리
        (
            "UPDATE emp SET sal = (SELECT AVG(sal) FROM emp_hist)",
            ["EMP", "EMP_HIST"],
        ),
        # 8. DELETE + 서브쿼리
        (
            "DELETE FROM emp WHERE id IN (SELECT id FROM to_delete)",
            ["EMP", "TO_DELETE"],
        ),
        # 9. DUAL 제외
        ("SELECT SYSDATE FROM DUAL", []),
        # 10. 딕셔너리 제외
        ("SELECT * FROM USER_TABLES", []),
        # 11. 동적 뷰 제외
        ("SELECT * FROM V$SESSION", []),
        # 12. 문자열 리터럴 오탐 없음
        ("SELECT * FROM EMP WHERE name = 'FROM DEPT'", ["EMP"]),
        # 13. 힌트 오탐 없음
        ("SELECT /*+ FULL(EMP) */ * FROM EMP", ["EMP"]),
        # 15. DB 링크 스트립
        ("SELECT * FROM EMP@DB1", ["EMP"]),
        # 16. 스키마 프리픽스 스트립
        ("SELECT * FROM SCOTT.EMP", ["EMP"]),
        # 17. UNION 양쪽
        (
            "SELECT * FROM EMP UNION SELECT * FROM EMP_ARCHIVE",
            ["EMP", "EMP_ARCHIVE"],
        ),
        # 18. 계층 쿼리
        ("SELECT * FROM EMP CONNECT BY PRIOR mgr_id = emp_id", ["EMP"]),
    ],
)
def test_extract_tables_success(sql: str, expected: list[str]) -> None:
    assert extract_tables(sql) == expected


def test_multiple_statements_rejected() -> None:
    # 14. 다중 문장 거부
    with pytest.raises(ExtractionError):
        extract_tables("SELECT * FROM emp; SELECT * FROM dept;")


def test_invalid_sql_raises_with_details() -> None:
    # 19. 파싱 실패
    with pytest.raises(ExtractionError) as exc_info:
        extract_tables("SELCT * FRM EMP")
    assert str(exc_info.value)


def test_empty_input_rejected() -> None:
    # 20. 빈 입력 방어
    with pytest.raises(ExtractionError):
        extract_tables("")
    with pytest.raises(ExtractionError):
        extract_tables("   \n\t  ")
