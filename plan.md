# Oracle SQL 테이블 추출 웹서비스 — 구현 계획

## 목적

개발자용 사내 웹툴. Oracle SQL 한 문장을 입력받아 참조된 물리 테이블 이름을 추출한다.
**용도: 데이터 이관 대상 파악.** 이관 담당자가 SQL을 붙여넣어 관련 테이블 리스트를 자동으로 확보한다.

## 스택

- **언어**: Python
- **웹 프레임워크**: FastAPI
- **SQL 파서**: sqlglot (dialect="oracle")
- **UI**: 단일 HTML 페이지 (텍스트박스 + 버튼 + 결과 리스트)

## 입력 사양

- Oracle SQL **단일 문장**
- 지원 문법: `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `MERGE`
- 최대 입력 크기: **1MB**
- **비지원 (모두 파싱 실패로 거부)**:
  - PL/SQL 블록 (프로시저, 함수, 트리거)
  - 동적 SQL (`EXECUTE IMMEDIATE ...`)
  - 세미콜론으로 이어진 다중 문장

## 처리 파이프라인

```
1. 입력 SQL 원본 수신 (변형 없음)
2. sqlglot.parse_one(sql, dialect="oracle") 로 AST 생성
3. sqlglot.optimizer.scope.build_scope() 로 스코프 분석
4. 각 스코프의 sources 중 실제 테이블 참조(exp.Table)만 수집
   - CTE alias 자동 제외
   - 인라인 뷰 alias 자동 제외
5. 스키마 프리픽스 / DB 링크 스트립
   - "SCOTT.EMP" → "EMP"
   - "EMP@DB1" → "EMP"
6. 하드코딩 제외 리스트 필터링
   - DUAL
   - USER_* (예: USER_TABLES)
   - ALL_* (예: ALL_OBJECTS)
   - DBA_*
   - V$*
   - GV$*
   - SYS.*
7. 추출 이름 upper() 정규화
8. 중복 제거 (set)
9. 알파벳 오름차순 정렬
10. 리스트 반환
```

## 출력 사양

**성공 응답**
```json
{
  "tables": ["DEPT", "EMP", "SALARY_HIST"]
}
```

**파싱 실패 응답**
- sqlglot `ParseError`의 위치(line, column) 및 원인(expected/found) 정보를 그대로 노출
```json
{
  "error": "Parse error at line 2, col 15: expected 'FROM' but found 'FRM'"
}
```

## UI

- 단일 페이지
- 상단 텍스트박스 (SQL 붙여넣기)
- "추출" 버튼
- 하단 결과 리스트 (성공 시) 또는 에러 메시지 (실패 시)
- **인증 없음** (사내망 한정)
- **SQL 내용 로깅 없음** (민감 데이터 가능성)

## 의도적 비스코프 (README에 반드시 명시)

이 툴은 텍스트 파싱만 수행하며, Oracle 데이터베이스에 접속하지 않는다. 따라서 다음은 처리 범위 밖이며, 이관 담당자가 별도 확인해야 한다.

1. **뷰/테이블 구분 안 함**
   - SQL에서 참조된 이름이 뷰인지 테이블인지 판별할 수 없음
   - 결과 리스트에 뷰 이름이 섞여 나올 수 있음
   - 이관 담당자가 결과 리스트를 검토하여 뷰를 걸러내야 함

2. **시노님 해석 안 함**
   - 프로젝트에서 시노님을 사용하지 않는다는 전제
   - 시노님이 발견되면 원본 이름 그대로 결과에 노출됨

3. **크로스 스키마 / 크로스 DB 참조가 하나로 뭉쳐 보임**
   - `SCOTT.EMP`, `HR.EMP`, `EMP@REMOTE_DB` 모두 `EMP` 하나로 표시됨
   - 이관 대상이 실제로는 다른 물리 테이블일 수 있음
   - **주의**: 이관 담당자는 SQL 원본을 병행 확인하여 크로스 스키마/DB 참조 여부를 확인해야 함

## 회귀 테스트 케이스 (릴리스 전 필수 통과)

| # | 입력 SQL | 기대 결과 | 검증 포인트 |
|---|---------|----------|-------------|
| 1 | `SELECT * FROM EMP e JOIN DEPT d ON e.id = d.id` | `["DEPT", "EMP"]` | alias 제외 |
| 2 | `WITH t AS (SELECT * FROM EMP) SELECT * FROM t JOIN DEPT ON t.id = DEPT.id` | `["DEPT", "EMP"]` | CTE alias 제외, 본문 테이블 포함 |
| 3 | `SELECT * FROM (SELECT id FROM EMP) x` | `["EMP"]` | 인라인 뷰 alias 제외 |
| 4 | `MERGE INTO target t USING source s ON (t.id=s.id) WHEN MATCHED THEN UPDATE SET t.v=s.v` | `["SOURCE", "TARGET"]` | MERGE 양쪽 |
| 5 | `MERGE INTO target USING (SELECT * FROM src) s ON (target.id=s.id) WHEN MATCHED THEN UPDATE SET v=s.v` | `["SRC", "TARGET"]` | MERGE USING 서브쿼리 |
| 6 | `INSERT ALL INTO t1 VALUES (1) INTO t2 VALUES (2) SELECT * FROM src` | `["SRC", "T1", "T2"]` | multi-table INSERT |
| 7 | `UPDATE emp SET sal = (SELECT AVG(sal) FROM emp_hist)` | `["EMP", "EMP_HIST"]` | UPDATE + 상관 서브쿼리 |
| 8 | `DELETE FROM emp WHERE id IN (SELECT id FROM to_delete)` | `["EMP", "TO_DELETE"]` | DELETE + 서브쿼리 |
| 9 | `SELECT SYSDATE FROM DUAL` | `[]` | DUAL 제외 |
| 10 | `SELECT * FROM USER_TABLES` | `[]` | 딕셔너리 제외 |
| 11 | `SELECT * FROM V$SESSION` | `[]` | 동적 뷰 제외 |
| 12 | `SELECT * FROM EMP WHERE name = 'FROM DEPT'` | `["EMP"]` | 문자열 리터럴 오탐 없음 |
| 13 | `SELECT /*+ FULL(EMP) */ * FROM EMP` | `["EMP"]` | 힌트 오탐 없음 |
| 14 | `SELECT * FROM emp; SELECT * FROM dept;` | 파싱 실패 반환 | 다중 문장 거부 |
| 15 | `SELECT * FROM EMP@DB1` | `["EMP"]` | DB 링크 스트립 |
| 16 | `SELECT * FROM SCOTT.EMP` | `["EMP"]` | 스키마 프리픽스 스트립 |
| 17 | `SELECT * FROM EMP UNION SELECT * FROM EMP_ARCHIVE` | `["EMP", "EMP_ARCHIVE"]` | UNION 양쪽 |
| 18 | `SELECT * FROM EMP CONNECT BY PRIOR mgr_id = emp_id` | `["EMP"]` | 계층 쿼리 |
| 19 | `SELCT * FRM EMP` (오타) | 파싱 실패 응답 (위치/원인 포함) | 파싱 에러 UX |
| 20 | `""` (빈 문자열) | 에러 응답 | 방어 |

## 구현 순서 (제안)

1. **프로젝트 스켈레톤** — FastAPI 프로젝트 구조, 의존성(`fastapi`, `uvicorn`, `sqlglot`, `pytest`) 설정
2. **핵심 추출 함수** — sqlglot 스코프 분석 기반 테이블 추출 로직 (`extract_tables(sql: str) -> list[str]`)
3. **회귀 테스트** — 위 20개 케이스를 pytest로 작성, 모두 통과 확인
4. **FastAPI 엔드포인트** — `POST /extract` (요청 크기 제한 1MB, 파싱 에러 처리)
5. **UI** — 단일 HTML 페이지 (텍스트박스 + 버튼 + 결과 표시)
6. **README** — 사용법 및 위 "의도적 비스코프" 섹션 명시

## 리스크 및 대응

| 리스크 | 대응 |
|--------|------|
| sqlglot Oracle 방언이 실무 SQL 문법을 100% 커버 못 함 | 파싱 실패 시 원본 에러 메시지를 담당자에게 안내. 자주 실패하는 패턴 발견 시 우회 로직 검토 |
| 뷰가 결과에 섞여 나와 이관 담당자가 놓침 | README 및 UI 하단에 "결과에 뷰가 포함될 수 있음" 안내 문구 상시 노출 |
| 크로스 스키마 참조를 담당자가 인지 못 함 | UI에 "SQL 원본에서 스키마 프리픽스, DB 링크(@) 여부를 반드시 확인하십시오" 경고 문구 노출 |
| 대용량 SQL 붙여넣기로 서버 부하 | FastAPI 미들웨어로 요청 본문 1MB 제한 |
