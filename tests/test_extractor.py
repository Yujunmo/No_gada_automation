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

        ("""
/******************************************************************************
 * 프로그램명 : 고객 종합 거래 조회
 * 작성일자   : 2026-07-05
 * 작성자     : SYSTEM
 *
 * 설명
 *  - VIP 고객의 최근 거래내역 및 위험등급 조회
 *  - 대출, 카드, 로그인 여부를 함께 조회
 ******************************************************************************/

WITH BASE_CUSTOMER AS (

    /* 고객 기본 정보 */
    SELECT /*+ MATERIALIZE */
           C.CUST_ID,
           C.CUST_NM,
           C.BRANCH_CD,
           C.REG_DT,
           C.STATUS_CD,
           A.ACCT_NO,
           A.PROD_CD,
           A.BALANCE
      FROM CUST_INFO C
           INNER JOIN ACCT_INFO A
               ON C.CUST_ID = A.CUST_ID
     WHERE C.STATUS_CD = 'A'
       AND A.USE_YN = 'Y'
),

TXN_SUM AS (

    /* 최근 3개월 거래 합계 */
    SELECT /*+ PARALLEL(T 4) */
           T.ACCT_NO,
           SUM(T.AMT) AS TOTAL_AMT,
           COUNT(*) AS TXN_CNT,
           MAX(T.TXN_DT) AS LAST_TXN_DT
      FROM TXN_HIST T
     WHERE T.TXN_DT >= ADD_MONTHS(SYSDATE,-3)
     GROUP BY T.ACCT_NO

),

VIP_CUSTOMER AS (

    /* VIP 고객만 추출 */

    SELECT B.*
      FROM BASE_CUSTOMER B
     WHERE B.BALANCE >= 10000000

)

SELECT /*+
           LEADING(V)
           USE_HASH(T)
           USE_NL(BR)
           INDEX(CA PK_CARD_INFO)
       */

       V.CUST_ID,
       V.CUST_NM,
       V.ACCT_NO,

       P.PROD_NM,

       BR.BRANCH_NM,

       E.EMP_NM,

       NVL(T.TOTAL_AMT,0) AS TOTAL_AMT,

       T.TXN_CNT,

       T.LAST_TXN_DT,

       R.RISK_GRADE,

       --------------------------------------------------------
       -- 카드 보유 여부
       --------------------------------------------------------
       CASE
            WHEN CA.CARD_NO IS NULL THEN 'N'
            ELSE 'Y'
       END AS CARD_YN,

       --------------------------------------------------------
       -- 대출 여부
       --------------------------------------------------------
       CASE
            WHEN L.LOAN_ID IS NULL THEN 'N'
            ELSE 'Y'
       END AS LOAN_YN,

       --------------------------------------------------------
       -- Scalar Sub Query
       --------------------------------------------------------
       (
           SELECT MAX(H.LOGIN_DT)
             FROM LOGIN_HIST H
            WHERE H.CUST_ID = V.CUST_ID
       ) AS LAST_LOGIN_DT,

       --------------------------------------------------------
       -- Scalar Sub Query
       --------------------------------------------------------
       (
           SELECT COUNT(*)
             FROM CARD_INFO X
            WHERE X.CUST_ID = V.CUST_ID
       ) AS CARD_CNT

FROM VIP_CUSTOMER V

LEFT JOIN TXN_SUM T
       ON V.ACCT_NO = T.ACCT_NO

LEFT JOIN PROD_INFO P
       ON V.PROD_CD = P.PROD_CD

LEFT JOIN BRANCH_INFO BR
       ON V.BRANCH_CD = BR.BRANCH_CD

LEFT JOIN EMP_INFO E
       ON BR.MGR_EMP_ID = E.EMP_ID

LEFT JOIN RISK_GRADE R
       ON V.CUST_ID = R.CUST_ID

LEFT JOIN LOAN_INFO L
       ON V.CUST_ID = L.CUST_ID
      AND L.LOAN_STATUS = 'NORMAL'

LEFT JOIN CARD_INFO CA
       ON V.CUST_ID = CA.CUST_ID
      AND CA.USE_YN = 'Y'

WHERE 1 = 1

/*------------------------------------------------------------
  최근 로그인 고객만 조회
-------------------------------------------------------------*/
AND EXISTS (

        SELECT 1
          FROM LOGIN_HIST LH
         WHERE LH.CUST_ID = V.CUST_ID
           AND LH.LOGIN_DT >= ADD_MONTHS(SYSDATE,-1)

)

/*------------------------------------------------------------
  상품 평균 잔액 이상 고객
-------------------------------------------------------------*/
AND V.BALANCE >

(
    SELECT AVG(A.BALANCE)
      FROM ACCT_INFO A
     WHERE A.PROD_CD = V.PROD_CD
)

/*------------------------------------------------------------
  위험등급이 존재하는 고객
-------------------------------------------------------------*/
AND V.CUST_ID IN (

    SELECT RG.CUST_ID
      FROM RISK_GRADE RG
     WHERE RG.RISK_GRADE IN ('A','B')

)

/*------------------------------------------------------------
  휴면계좌 제외
-------------------------------------------------------------*/
AND NOT EXISTS (

    SELECT 1
      FROM ACCT_INFO AX
     WHERE AX.ACCT_NO = V.ACCT_NO
       AND AX.STATUS_CD = 'D'

)

GROUP BY

       V.CUST_ID,
       V.CUST_NM,
       V.ACCT_NO,
       P.PROD_NM,
       BR.BRANCH_NM,
       E.EMP_NM,
       T.TOTAL_AMT,
       T.TXN_CNT,
       T.LAST_TXN_DT,
       R.RISK_GRADE,
       CA.CARD_NO,
       L.LOAN_ID

HAVING

       NVL(T.TOTAL_AMT,0) >= 500000

ORDER BY

       T.TOTAL_AMT DESC,
       V.CUST_ID;


""",[
  "ACCT_INFO",
  "BRANCH_INFO",
  "CARD_INFO",
  "CUST_INFO",
  "EMP_INFO",
  "LOAN_INFO",
  "LOGIN_HIST",
  "PROD_INFO",
  "RISK_GRADE",
  "TXN_HIST"
])
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
