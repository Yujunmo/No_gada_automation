# Oracle SQL 테이블 추출 웹서비스

Oracle SQL 한 문장에서 참조된 물리 테이블 이름을 추출하는 사내 개발자용 툴.
데이터 이관 대상 파악에 사용한다.

- **입력**: Oracle SQL 단일 문장 (SELECT / INSERT / UPDATE / DELETE / MERGE, 최대 1MB)
- **출력**: 알파벳 정렬된 대문자 테이블 이름 리스트
- **파서**: sqlglot (dialect="oracle") — DB 접속 없음

전체 사양과 회귀 케이스는 [`plan.md`](./plan.md) 참고.

---

## 목차

- [빠른 시작](#빠른-시작)
- [사용 예시](#사용-예시)
- [API](#api)
- [처리 파이프라인](#처리-파이프라인)
- [프로젝트 구조](#프로젝트-구조)
- [테스트](#테스트)
- [처리 범위 밖 (주의사항)](#처리-범위-밖-주의사항)
- [트러블슈팅](#트러블슈팅)

---

## 빠른 시작

**요구사항**: Python 3.9+

```bash
# 1. 가상환경 및 의존성 설치
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

# 2. 개발 서버 실행
uvicorn app.main:app --reload

# 3. 브라우저 접속
open http://localhost:8000
```

브라우저에서 텍스트박스에 SQL을 붙여넣고 "추출" 버튼을 누르면 테이블 리스트가 표시된다.

---

## 사용 예시

**입력**
```sql
MERGE INTO target t
USING (SELECT * FROM src) s
ON (t.id = s.id)
WHEN MATCHED THEN UPDATE SET t.v = s.v
```

**결과**
```
SRC
TARGET
```

CTE와 인라인 뷰의 alias는 자동 제외된다.

**입력**
```sql
WITH filtered AS (SELECT * FROM EMP WHERE dept_id = 10)
SELECT * FROM filtered JOIN DEPT ON filtered.dept_id = DEPT.id
```

**결과**
```
DEPT
EMP
```

(`filtered`는 CTE alias라 제외됨)

---

## API

### `POST /extract`

**요청**
```http
POST /extract HTTP/1.1
Content-Type: application/json

{"sql": "SELECT * FROM EMP e JOIN DEPT d ON e.id=d.id"}
```

**성공 응답 (200)**
```json
{"tables": ["DEPT", "EMP"]}
```

**실패 응답**

| 상태 | 상황 | 예시 |
|------|------|------|
| 400 | 파싱 실패 / 다중 문장 / 지원 안 하는 문법 / 빈 입력 | `{"detail": "Parse error at line 1, col 15: ..."}` |
| 413 | 입력 SQL 1MB 초과 | `{"detail": "SQL exceeds 1MB limit"}` |
| 422 | 요청 body 스키마 오류 | FastAPI 기본 응답 |

**curl 예시**
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT * FROM EMP e JOIN DEPT d ON e.id=d.id"}'
# → {"tables":["DEPT","EMP"]}
```

---

## 처리 파이프라인

```
SQL 텍스트 입력 (원본 유지)
  ↓
sqlglot.parse(sql, dialect="oracle")
  ↓
검증
  - 빈 입력 거부
  - 문장 수 == 1 확인 (아니면 거부)
  - 최상위 노드가 Select/Insert/Update/Delete/Merge/Union/MultitableInserts 확인
  ↓
CTE 이름 수집 (find_all(exp.CTE))
  ↓
모든 exp.Table 노드 순회
  - CTE 이름과 매칭되면 제외 (CTE alias)
  - @ 뒤의 DB 링크 스트립: EMP@DB1 → EMP
  - 스키마 프리픽스는 sqlglot이 .name에서 자동 제거: SCOTT.EMP → EMP
  - 대문자 변환
  - 제외 목록 필터: DUAL, USER_*, ALL_*, DBA_*, V$*, GV$*, SYS.*
  ↓
중복 제거 → 알파벳 정렬 → 리스트 반환
```

인라인 뷰 alias (`FROM (SELECT ...) x`의 `x`)는 sqlglot AST에서 `TableAlias` 노드로 표현되어 `exp.Table` 순회에 잡히지 않으므로 별도 처리 없이 자동 제외된다.

---

## 프로젝트 구조

```
.
├── plan.md                  # 사양 및 회귀 케이스
├── pyproject.toml           # 의존성 (fastapi, uvicorn, sqlglot) + dev(pytest, httpx)
├── README.md
├── app/
│   ├── main.py              # FastAPI 엔드포인트 (POST /extract, 1MB 제한)
│   ├── extractor.py         # 핵심 추출 로직 (extract_tables, ExtractionError)
│   └── static/index.html    # UI (텍스트박스 + 버튼 + 결과)
└── tests/
    └── test_extractor.py    # 회귀 케이스 20개 (pytest)
```

---

## 테스트

```bash
pytest
```

`plan.md`에 정의된 20개 회귀 케이스가 모두 통과하는 것을 릴리스 기준으로 삼는다.

새로운 실무 SQL에서 오추출/누락 사례가 발견되면 **먼저 `tests/test_extractor.py`에 케이스로 추가**한 뒤 `extractor.py`를 고치는 것을 원칙으로 한다 (회귀 방지).

---

## 처리 범위 밖 (주의사항)

이 툴은 텍스트 파싱만 수행하며 Oracle DB에 접속하지 않는다. 다음은 원리적으로 처리 불가하므로 이관 담당자가 별도 확인해야 한다.

### 1. 뷰/테이블 구분 안 함
SQL에 등장한 이름이 뷰인지 물리 테이블인지 알 방법이 없다.
- 결과 리스트에 뷰 이름이 섞여 나올 수 있음
- 이관 대상은 물리 테이블이므로, 담당자가 결과를 검토하여 뷰를 걸러내야 함

### 2. 시노님 해석 안 함
프로젝트에서 시노님을 사용하지 않는다는 전제. 시노님이 발견되면 원본 이름 그대로 결과에 노출됨.

### 3. 크로스 스키마 / 크로스 DB 참조가 하나로 뭉쳐 보임
`SCOTT.EMP`, `HR.EMP`, `EMP@REMOTE_DB`가 모두 `EMP` 하나로 표시된다.
- 이관 대상이 실제로는 다른 물리 테이블일 수 있음
- **SQL 원본에서 스키마 프리픽스(`.`)와 DB 링크(`@`) 여부를 반드시 확인할 것**

### 4. PL/SQL, 동적 SQL 미지원
프로시저/함수/트리거 본문 및 `EXECUTE IMMEDIATE`는 스코프 밖.
- 입력으로 들어오면 파싱 실패 (400)


---

## 트러블슈팅

**Q. `pip install`이 `Package requires Python >=3.9` 로 실패**
- 시스템 Python 버전 확인: `python3 --version`
- macOS 시스템 Python 3.9로도 동작함

**Q. Homebrew Python (3.12, 3.14)에서 venv 생성 실패 (`pyexpat` 관련)**
- macOS 시스템 libexpat과 Homebrew Python 사이 호환성 이슈
- 해결: 시스템 Python (`/usr/bin/python3`) 사용

**Q. 파싱 실패인데 SQL이 문법상 맞는 것 같다**
- sqlglot의 Oracle 방언 커버리지 구멍일 수 있음
- 응답의 `detail` 필드에 위치와 원인 정보 포함됨
- 새로운 사각지대 발견 시 `tests/test_extractor.py`에 케이스 추가 후 처리 로직 확장

**Q. 결과에 있어야 할 테이블이 안 나온다**
- 해당 SQL을 최소 재현 케이스로 만들어 `tests/test_extractor.py`에 추가
- `extractor.py`의 `find_all(exp.Table)` 순회에서 놓친 노드 타입 확인 (예: 특수 DML 구문)
