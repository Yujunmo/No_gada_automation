# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**No_Gada** — 반복 수작업("노가다")을 없애기 위한 **Oracle 전용** 사내 자동화 툴킷. 여러 도구를 좌측 사이드바로 전환하는 **단일 FastAPI 웹 서비스**다. 각 도구는 백엔드(`app/tools/<name>/`)와 프론트(`app/static/tools/<name>/`) 한 쌍으로 독립 구성된다.

| 도구 | 모듈 | 기능 | 상태 |
|------|------|------|------|
| **SQL Bench** | `sql_bench` | 붙여넣은 Oracle SQL → 참조 테이블 추출 | 구현됨 |
| **Table Extractor** | `table_extractor` | 서비스/DBIO ID → 원격지(FTP) 소스 스캔 → 참조 테이블 전체 추출 | 준비 중 |

사이드바에는 `SQL Formatter`, `Migration Builder`도 "준비중"으로 자리만 잡혀 있다. 향후 문법 체크, DB 링크 부착/제거, 대소문자 치환 등이 추가될 예정.

## 명령어

```bash
# 설치 (Python 3.9+)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 개발 서버 (http://localhost:8000)
uvicorn app.main:app --reload

# 전체 테스트 (pyproject에 -v 기본 적용)
pytest

# 단일 테스트 / 필터
pytest tests/tools/test_sql_bench.py::test_multiple_statements_supported
pytest -k dual
```

린터/타입체커는 설정돼 있지 않다(테스트만이 게이트).

## 아키텍처 (큰 그림)

### 멀티툴 플러그인 구조
`app/main.py`가 각 도구의 `router`를 `include_router`로 붙이고, 마지막에 `StaticFiles`를 `/`에 마운트한다. **정적 파일 마운트는 반드시 라우터 뒤**에 와야 API 경로가 가려지지 않는다. 각 도구 라우터는 자기 네임스페이스를 갖는다: `APIRouter(prefix="/sql-bench")` → `POST /sql-bench/extract`.

### 새 도구 추가 레시피 (여러 파일에 걸침)
1. `app/tools/<name>/`에 `__init__.py`, `router.py`(`APIRouter(prefix="/<name>")`), 필요 시 `service.py`.
2. `app/main.py`에서 라우터 import + `include_router`.
3. `app/static/tools/<name>/`에 `<name>.js` / `<name>.css`.
4. `app/static/index.html`: 사이드바에 `<a data-page="<name>">` nav 항목 + `<div id="page-<name>">` 컨테이너 추가, `<head>`/하단에 css·js 링크 추가.

### 프론트엔드 규약 (프레임워크 없음, 순수 JS)
- `app/static/js/app.js`가 `.nav-item[data-page="X"]` 클릭 시 `#page-X` 컨테이너만 표시하고 나머지를 숨긴다. 공용 헬퍼 `App.showToast` / `App.copyToClipboard` 제공.
- 각 도구 JS는 자기 `#page-<name>` 컨테이너를 찾아 `innerHTML`을 주입하고, 자기 엔드포인트(`/<name>/...`)로 `fetch`한다. 즉 **`data-page` 값 = 컨테이너 id 접미사 = 도구 이름**으로 세 곳이 묶여 있다.

### SQL Bench 처리 파이프라인 (`app/tools/sql_bench/service.py`)
`extract_tables(sql) -> list[str]`:
1. 빈 입력 방어 → `ExtractionError`.
2. **`sanitize_text`(공용)로 보이지 않는 유니코드 문자 제거/정규화** — 제거 시 WARNING 로그. 복붙된 BOM·제로폭공백은 파싱오류 또는 조용한 오추출을 유발하므로 파싱 전에 반드시 거른다.
3. `sqlglot.parse(sql, dialect="oracle")` — **다중 문장 지원**(`;`로 나뉜 각 문장의 테이블을 합산, 중복 제거).
4. 문장별로 `exp.Table` 순회하며 이름 정규화(대문자화, `@dblink` 스트립; 스키마 프리픽스는 sqlglot이 `t.name`에서 이미 분리).
5. 제외: CTE alias(WITH절), `DUAL`, 딕셔너리/동적 뷰 접두사(`USER_`,`ALL_`,`DBA_`,`V$`,`GV$`,`SYS.`). 인라인 뷰 alias는 `TableAlias` 노드라 애초에 `exp.Table` 순회에 안 잡혀 자동 제외.
6. 정렬된 대문자 리스트 반환.

`POST /sql-bench/extract`: `{"sql":"..."}` → `{"tables":[...]}`. 1MB 초과 413, 파싱 오류 400.

### 공용 모듈 `app/common/`
툴 횡단 관심사를 둔다. 현재 `text.py`의 `sanitize_text(text) -> (cleaned, removed)`:
유니코드 카테고리 기준으로 `Cf`(제로폭·BOM·소프트하이픈·방향마크) 제거, `Zs`(NBSP·전각공백) → 일반 공백, 탭/개행은 보존. **멱등**이라 경계(라우터)에서 다시 호출해도 무해 — 향후 "제거된 문자 UI 노출"이 필요하면 라우터가 별도로 호출해 `removed`를 얻어도 된다. Table Extractor(원격 파일)도 재사용 대상.

### 로깅
로거 이름은 `no_gada.<tool>` 계층(예: `no_gada.sql_bench`). `main.py`에서 콘솔 + `RotatingFileHandler`(`logs/no_gada.log`, 5MB×5)를 붙이고, **루트=INFO, `no_gada`=DEBUG**로 설정해 서드파티 DEBUG 노이즈는 억제하고 앱 로그만 상세히 남긴다. `logs/`는 gitignore.

## 프로젝트 구조

```
app/
  main.py                     # FastAPI 앱 조립 + 로깅 설정
  common/text.py              # sanitize_text (툴 공용 텍스트 정제)
  tools/<tool>/router.py|service.py   # 툴별 백엔드
  static/
    index.html                # 사이드바 + 툴별 page 컨테이너
    js/app.js                 # nav 전환 + 공용 헬퍼
    css/ , tools/<tool>/      # 공용/툴별 스타일·스크립트
tests/
  common/test_text.py         # sanitize_text 단위 테스트
  tools/test_sql_bench.py     # SQL Bench 회귀 케이스
pyproject.toml                # name=no-gada, deps: fastapi/uvicorn/sqlglot
```

## 처리 범위 밖 (SQL Bench 한계 — README 상세)

순수 텍스트 파싱이라 DB에 접속하지 않는다. 따라서: **뷰와 물리 테이블을 구별 못 함**, 시노님 미해석, `SCOTT.EMP`·`HR.EMP`·`EMP@REMOTE`가 모두 `EMP` 하나로 뭉침(원본에서 스키마·DB링크 직접 확인 필요), PL/SQL·동적 SQL 미지원.

## 작업 원칙

- **회귀 우선**: 새 오추출/누락 사례가 나오면 먼저 `tests/`에 케이스를 추가하고 나서 `service.py`를 고친다. 전체 회귀 케이스 사양은 `plan.md` 참고.
- 이름 관련: 코드 모듈명 `sql_bench`/`table_extractor`는 화면 이름 "SQL Bench"/"Table Extractor"와 매핑되며, 라우트 prefix·`data-page`·정적 디렉토리가 모두 이 이름으로 묶여 있으니 리네이밍 시 함께 바꿔야 한다.
