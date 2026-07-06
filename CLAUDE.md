# No_gada_automation — Oracle SQL Table Extractor

Oracle SQL 한 문장을 입력받아 참조 테이블 목록을 추출하는 웹 서비스.

## 프로젝트 구조

```
app/
  extractor.py     # 핵심 파싱 로직 (sqlglot Oracle dialect)
  main.py          # FastAPI 서버 — POST /extract
  static/index.html  # 단순 HTML 프론트엔드
tests/
  test_extractor.py  # 회귀 케이스 20개
pyproject.toml
```

## 개발 환경

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## 자주 쓰는 명령어

```bash
# 서버 실행
uvicorn app.main:app --reload

# 테스트
pytest
```

## 핵심 동작

**`extract_tables(sql) -> list[str]`** (`app/extractor.py`)

- Oracle dialect로 파싱 (`sqlglot`)
- 단일 문장만 허용 (복수 문장 → `ExtractionError`)
- 지원 문장: SELECT, INSERT, UPDATE, DELETE, MERGE, UNION, multi-table INSERT
- 제외 대상:
  - `DUAL`
  - `USER_`, `ALL_`, `DBA_`, `V$`, `GV$`, `SYS.` 접두사
  - CTE 이름 (WITH절 alias)
- DB 링크(`@DB1`), 스키마 프리픽스(`SCOTT.EMP`) 제거 후 테이블명만 반환
- 결과: 대문자 정렬 리스트

**`POST /extract`** (`app/main.py`)

- Request: `{"sql": "..."}`
- Response: `{"tables": ["TABLE_A", ...]}`
- 1MB 초과 시 HTTP 413, 파싱 오류 시 HTTP 400

## 테스트 케이스 목록 (plan.md 기준)

| # | 케이스 |
|---|--------|
| 1 | alias 제외 |
| 2 | CTE alias 제외, 본문 테이블 포함 |
| 3 | 인라인 뷰 alias 제외 |
| 4 | MERGE 양쪽 테이블 |
| 5 | MERGE USING 서브쿼리 |
| 6 | multi-table INSERT |
| 7 | UPDATE + 상관 서브쿼리 |
| 8 | DELETE + 서브쿼리 |
| 9 | DUAL 제외 |
| 10 | 딕셔너리 뷰 제외 (USER_TABLES) |
| 11 | 동적 뷰 제외 (V$SESSION) |
| 12 | 문자열 리터럴 오탐 없음 |
| 13 | 힌트 오탐 없음 |
| 14 | 다중 문장 거부 |
| 15 | DB 링크 스트립 |
| 16 | 스키마 프리픽스 스트립 |
| 17 | UNION 양쪽 |
| 18 | 계층 쿼리 (CONNECT BY) |
| 19 | 파싱 실패 시 오류 메시지 포함 |
| 20 | 빈 입력 방어 |
