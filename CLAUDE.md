# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**No_Gada** — 반복 수작업("노가다")을 없애기 위한 **Oracle 전용** 사내 자동화 툴킷. 여러 도구를 좌측 사이드바로 전환하는 **단일 FastAPI 웹 서비스**다. 각 도구는 백엔드(`app/tools/<name>/`)와 프론트(`app/static/tools/<name>/`) 한 쌍으로 독립 구성된다.

| 도구 | 모듈 | 기능 | 상태 |
|------|------|------|------|
| **SQL Bench** | `sql_bench` | 붙여넣은 Oracle SQL → 참조 테이블 추출 | 구현됨 |
| **Table Extractor** | `table_extractor` | module_type/resource_group/file_id → 원격지(SFTP) 소스 읽기 → 참조 테이블 추출 | **DBIO 구현됨**, Service/Batch/Biz 준비 중 |

사이드바에는 `SQL Formatter`, `Migration Builder`도 "준비중"으로 자리만 잡혀 있다. 향후 문법 체크, DB 링크 부착/제거, 대소문자 치환 등이 추가될 예정.

## 명령어

```bash
# 설치 (Python 3.9+)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 개발 서버 (http://localhost:8000)
uvicorn app.main:app --reload

# Table Extractor 수동 검증용 로컬 SFTP (회사 서버 대역, 127.0.0.1:2222 testuser/testpass)
(cd remote_ap_server && docker compose up -d)   # 정지: docker compose down

# 데이터 조회용 로컬 MySQL (회사 DB 대역, 127.0.0.1:3306 testuser/testpass, DB=nogada)
(cd remote_db_server && docker compose up -d) # 정지: docker compose down / 초기화: down -v

# 전체 테스트 (pyproject에 -v 기본 적용, 현재 100여 개 수집)
pytest

# 단일 테스트 / 필터
pytest tests/tools/test_sql_bench.py::test_multiple_statements_supported
pytest -k dual
```

린터/타입체커는 설정돼 있지 않다(테스트만이 게이트). 단위/통합 테스트는 네트워크 없이 인메모리 fake reader로 돌므로 SFTP 없이도 `pytest`가 통과한다 — Docker SFTP는 브라우저/`curl` 수동 검증에만 필요.

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

### 테이블 추출 파이프라인 (`app/common/sql.py`)
테이블 추출은 **공용 모듈**(`app/common/sql.py`)에 있고 `sql_bench` 라우터와 `table_extractor`가 함께 import한다(도구 간 직접 의존 없음). 클래스가 아니라 상태 없는 모듈 함수 묶음이다.
`extract_tables(sql) -> list[str]`:
1. 빈 입력 방어 → `ExtractionError`.
2. **`sanitize_text`(공용)로 보이지 않는 유니코드 문자 제거/정규화** — 제거 시 WARNING 로그. 복붙된 BOM·제로폭공백은 파싱오류 또는 조용한 오추출을 유발하므로 파싱 전에 반드시 거른다.
3. **`strip_db_links`(공용)로 `@dblink` 참조를 텍스트 단계에서 제거** — `테이블@링크`뿐 아니라 `테이블 @ 링크`(공백 허용, 실제 Oracle 문법)도 잡는다. sqlglot이 `@` 앞 공백에서 파싱 실패하므로 **파싱 전 전처리**로 넣는다. 따옴표 문자열·주석(`--`, `/* */`) 내부의 `@`는 상태 기계로 보존(이메일 등 오탐 방지). 제거 시 DEBUG 로그.
4. `sqlglot.parse(sql, dialect="oracle")` — **다중 문장 지원**(`;`로 나뉜 각 문장의 테이블을 합산, 중복 제거).
5. 문장별로 `exp.Table` 순회하며 이름 정규화(대문자화; db link는 3에서 이미 제거됨, 스키마 프리픽스는 sqlglot이 `t.name`에서 이미 분리).
6. 제외: CTE alias(WITH절), `DUAL`, 딕셔너리/동적 뷰 접두사(`USER_`,`ALL_`,`DBA_`,`V$`,`GV$`,`SYS.`). 인라인 뷰 alias는 `TableAlias` 노드라 애초에 `exp.Table` 순회에 안 잡혀 자동 제외.
7. 정렬된 대문자 리스트 반환.

`POST /sql-bench/extract`: `{"sql":"..."}` → `{"tables":[...]}`. 1MB 초과 413, 파싱 오류 400.

### 공용 모듈 `app/common/`
툴 횡단 관심사를 둔다.
- `text.py`의 `sanitize_text(text) -> (cleaned, removed)`: 유니코드 카테고리 기준으로 `Cf`(제로폭·BOM·소프트하이픈·방향마크) 제거, `Zs`(NBSP·전각공백) → 일반 공백, 탭/개행은 보존. **멱등**이라 경계(라우터)에서 다시 호출해도 무해 — 향후 "제거된 문자 UI 노출"이 필요하면 라우터가 별도로 호출해 `removed`를 얻어도 된다.
- `sql.py`의 `extract_tables` / `ExtractionError`: Oracle SQL 테이블 추출(위 파이프라인 참고). `sql_bench`·`table_extractor` 공용.
- `sql.py`의 `strip_db_links(sql) -> (cleaned, links)`: `@dblink` 텍스트 제거(문자열·주석 내부 `@` 보존). `extract_tables`가 파싱 전처리로 호출하며, `sanitize_text`처럼 `(cleaned, removed)` 형태라 향후 "제거된 링크 UI 노출"에 재사용 가능.
- `proframe.py`의 `Module_Type` / `ResourceGroup`(`Literal` 타입): ProFrame ID 분류 체계(`dbio/service/batch/biz`, 업무그룹 `PCSP/PCSH/NCOM/NCSP/PCOM/PPFR/RLGR`). module_type 4종 전체에 걸친 값이라 공용에 둠 — `table_extractor`가 먼저 쓰지만 다른 툴(예: Migration Builder)도 소비처가 될 예정.
- `dbio.py`의 `read_dbio_xml(file_id, reader) -> str` / `classify_sqltype(file_id) -> str` / `UnknownSqlType`: DBIO ID로 원격 XML을 읽는 범용 동작. 실물 파일이 `release/dbio/xml/<ID>.xml`로 **평면 배치**(`DBIO_RESOURCE_ROOT`)라 경로는 `{ROOT}/<ID>.xml` 1회 조합·조회로 끝난다. PROG/SQLTYPE은 경로에 쓰이지 않지만, `classify_sqltype`(`SQL_TYPE_BY_SUFFIX`/`ID_SUFFIX_RE`, ID 끝 2글자 코드)로 **접미사가 인식 가능한 DBIO ID인지 검증**해 잘못된 ID를 파일없음(404)보다 명확한 400으로 먼저 거른다. "DBIO ID → 원격 XML"은 table_extractor만이 아니라 소비처가 늘어날 동작이라 공용화(단순 값이 아니라 로직까지 포함 — `proframe.py`와 달리 이 모듈은 동작 단위로 공용).
- `source.py`의 `SourceReader`(Protocol) / `SftpSourceReader` / `SourceNotFound`·`SourceError` / `default_reader()`: 원격 소스 I/O 인프라(경로→내용 문자열). 회사 서버가 SFTP라 paramiko 기반. `default_reader()`는 env(`NOGADA_SFTP_HOST/_PORT/_USER/_PASS/_BASE`, 기본값 `remote_ap_server` Docker SFTP 127.0.0.1:2222)에서 `SftpSourceReader`를 조립하는 팩토리 — 회사 SFTP 서버는 하나뿐이라 여러 툴이 공유. 라우터에 `Depends(default_reader)`로 주입하면 테스트에서 `app.dependency_overrides`로 인메모리 fake reader 교체 가능.
- `schema.py`의 `fetch_pk_columns(tables, db) -> {테이블: [PK컬럼]}`: `nogada.all_tables`(테이블→PK컬럼 매핑, 복합키는 여러 행)를 **1회 쿼리**로 조회해 테이블별 PK 컬럼을 돌려주는 딕셔너리 조회 도메인 로직. 입력을 대문자·중복 정규화하고 요청한 모든 테이블을 키로 포함(딕셔너리에 없으면 `[]`), 컬럼 순서는 DB 행 순서 보존. `db.py`(I/O) 위에 얹힌 층 — `dbio.read_dbio_xml`이 `source.py` 위에 얹힌 것과 동일 구조. table_extractor의 `/pks`가 먼저 쓰지만 다른 툴 재사용 대비 공용.
- `db.py`의 `DbClient`(Protocol) / `MySqlDbClient` / `DbError`·`QueryError` / `default_db()`: 원격 DB I/O 인프라(SQL→결과 행 `list[dict]`). `source.py`와 쌍둥이 구조 — "SQL을 주면 행을 돌려준다" 한 가지 동작만. **실제 대상은 회사 Oracle이나 용도가 단순 조회라 방언 무관을 전제**해 방언 변환 없이 순수 I/O + 테스트 주입용 경계일 뿐이다(반입 시 `MySqlDbClient`를 같은 인터페이스의 Oracle 구현으로 교체 + 접속정보만 변경). `default_db()`는 env(`NOGADA_DB_HOST/_PORT/_USER/_PASS/_NAME`, 기본값 `remote_db_server` Docker MySQL 127.0.0.1:3306/nogada testuser)에서 조립하는 팩토리. `query`마다 접속/해제하는 상태 없는 모델, `DictCursor`로 행 반환, 읽기 전용(커밋 안 함). 접속 실패는 `DbError`, SQL 실행 실패는 `QueryError`로 구분. 라우터에 `Depends(default_db)`로 주입 → 테스트는 인메모리 fake client로 교체. 소비처: `schema.fetch_pk_columns`(그 위에서 `table_extractor`의 `/pks`·`/migrate-sql`가 사용).

### Table Extractor 파이프라인 (DBIO 경로)
`sql_bench`가 SQL 텍스트를 직접 받는 반면, `table_extractor`는 **식별자(module_type/(resource_group)/file_id)로 원격 파일을 찾아 읽은 뒤** 그 안의 SQL을 `extract_tables`(공용)로 넘긴다. REST 계약은 부작용 없는 조회라 경로 파라미터 GET(바디 없음)이며, **`resource_group`은 옵셔널**이다 — 같은 핸들러에 라우트 2개를 붙여 **DBIO는 `GET /table-extractor/{module_type}/{file_id}`(2세그먼트, resource_group 생략)**, **그 외(Service/Batch/Biz)는 `GET /table-extractor/{module_type}/{resource_group}/{file_id}`(3세그먼트)**로 받는다. DBIO는 resource_group을 파일 경로에 쓰지 않아 생략하고(3세그먼트로 줘도 하위호환으로 동작하며 값은 무시), 프론트는 module_type이 dbio면 세그먼트를 빼고 콤보박스도 숨긴다. `module_type`/`resource_group`은 `Literal`(공용 `proframe.py`)이라 잘못된 값은 FastAPI가 422로 자동 거부(`resource_group`은 `Optional`이라 생략은 허용).

흐름: `router.py`(`Depends(default_reader)`로 SFTP reader 주입) → `service.extract(module_type, resource_group, file_id, reader)`:
1. 지금은 `module_type == "dbio"`만 처리(그 외는 라우터가 501). Service/Batch/Biz는 상위 `.c` 소스에서 하위 ID를 스캔·재귀 해석하는 후속 작업(`plan.md` 참고).
2. `dbio.read_dbio_xml`(공용): ID 접미사(끝 2글자 코드)를 `classify_sqltype`로 검증 → `release/dbio/xml/<ID>.xml` 평면 경로 1회 조합 → `reader.read()`. 인식 못 하는 접미사는 `UnknownSqlType`(→라우터 400).
3. `mapper.extract_sql`(table_extractor 전용): ProFrame published XML에서 `<sqlString>` 텍스트 수집(루트 태그/네임스페이스 무관하게 로컬네임 매칭, 파싱 실패 시 정규식 폴백). 바인드는 이미 Oracle `:name`이라 치환 없음.
4. 각 SQL을 `extract_tables`로 돌려 **테이블 합집합**(정렬). 응답 `{tables, sql, dbios}`.

에러 매핑(라우터): `UnknownSqlType`/`ExtractionError`→400, `SourceNotFound`→404, `module_type != dbio`→501. (`SourceError` 접속실패는 아직 매핑 안 돼 500 — 후속 502/503 예정.)

**`POST /table-extractor/pks`**: `{tables:[...]}` → `{pks:{테이블:[PK컬럼]}}`. 추출과 분리된 조회로, 프론트가 추출 직후 전체 테이블 목록으로 1회 호출해 캐시하고 선택 변경 시 **PK 합집합**을 클라이언트에서 계산한다(매 선택마다 서버 조회 안 함). `Depends(default_db)`로 DB 주입, `schema.fetch_pk_columns` 호출. 에러 매핑: `DbError`→503, `QueryError`→500. 프론트(`table_extractor.js`): **필터된(보이는) 테이블 목록이 곧 이관 대상**(별도 선택 체크박스 없음 — 텍스트/접두사 필터·삭제로 좁힘). 이관 sql 위 키 입력란은 그 대상들의 **PK 합집합**(중복 제거·첫 등장 순서)을 실시간 표시.
- **날짜 PK**: 컬럼명이 `date`로 끝나면(사내 관행) 날짜 필드로 보고 **[단일|기간] 토글** 제공(YYYYMMDD 8자리). 입력 상태는 `keyinState`(컬럼별 `{isDate,mode,value|single|from|to}`)에 보존돼 필터·재렌더에도 유지.
- **이관 SQL 생성**: 'FROM 링크(원격 소스)' + 'TO 링크(대상)' 입력 + '이관 SQL 생성' 버튼 → 프론트는 `keyinState`를 컬럼별 조건(`eq`/`between`)으로 변환해 **`POST /table-extractor/migrate-sql`** 호출, 응답을 **팝업(모달)** 으로 표시(인라인 textarea 없음). 각 테이블은 **자기 PK 컬럼만**(all_tables 조회) AND 결합, 값은 전부 문자열 따옴표(`''` 이스케이프), 단일=`=`/기간=`BETWEEN`. 값 미입력 컬럼은 조건절에서 제외(주석 표기), 한 테이블 키가 전부 비면 전체삭제 방지로 제외, PK없음 테이블 제외, COMMIT 없음.
- **팝업 그룹 박스**: 생성 SQL을 **테이블 접미사별 박스**로 나눠 담는다 — `_BS`/`_HT`/`_MA`/`_SM`/`_TR` 순, 그 외는 `기타`(비어 있는 그룹 생략). 박스마다 개별 복사 + 모달 '전체 복사'. **이관 SQL이 생성되지 않은 테이블**(PK없음 `no_pk` + 키 미매칭 `skipped`)은 모달 하단 **표**(1열 테이블명 / 2열 사유: "PK 정보 없음" · "입력 키와 PK 미매칭")로 표시. 모달은 X/배경클릭/Esc로 닫힘.

**`POST /table-extractor/migrate-sql`**: `{tables, from_link, to_link, keys:{컬럼:{op,value|start,end}}}` → `{sql, generated, skipped, no_pk, groups:[{key,sql,tables}]}`. 생성 형태는 `DELETE FROM t@<TO> WHERE ...` + `INSERT INTO t@<TO> SELECT * FROM t@<FROM> WHERE ...` (FROM=원격 소스에서 읽어 TO=대상에 넣음, TO 비우면 로컬, 링크 앞 `@` 중복 제거). `groups`는 접미사(`migrate.GROUP_ORDER`+기타)별로 묶은 SQL(팝업 박스용). 계층: **라우터**(요청 모델 검증, `KeyCondIn`→`migrate.KeyCond` 변환, 에러 매핑 `DbError`→503·`QueryError`→500, 응답 형태) → **`service.migrate_sql`**(오케스트레이션: 테이블명 대문자 정규화 + `schema.fetch_pk_columns`로 PK 조회 + 순수 함수 호출, `Depends(default_db)` 주입) → **순수 함수 `migrate.build_migration_sql`**(DB·HTTP 비의존, 그룹핑 포함, `tests/tools/test_migrate.py`로 고정)로 조립. (`extract`와 동일한 router→service 패턴.)

프론트(`table_extractor.js`): `#te-submit` 클릭 → 경로 조합해 `fetch` → **좌측 패널** = 테이블 목록(실시간 텍스트 필터 + `TRU/PFO/PTN/RPT` 접두사 필터 + 개별 삭제 + 전체/개별 복사, `FEP` 접두사는 이관 미지원이라 하단에 읽기 전용 분리). **우측 패널** = PK 키 입력 + 이관 SQL 생성(위 `/pks`·`/migrate-sql` 항목 참고). 업무그룹 입력은 7개 값(`ResourceGroup`)을 필터링하는 검색형 콤보박스.

**재귀 참조 제외 목록**: `service.extract_from_module`이 service/batch/biz 소스를 재귀적으로 훑다가 "참조로 만나는" DBIO/모듈 ID 중 항상 집계에서 빼고 싶은 게 있으면 `config/excluded_refs.txt`(한 줄에 ID 하나, `#` 주석, 경로는 `NOGADA_EXCLUDED_REFS_PATH`로 override)에 등록한다. 로더는 `app/tools/table_extractor/excludes.py::load_excluded_refs`(파일 없으면 빈 set). **최상위로 직접 요청한 ID는 이 목록과 무관하게 항상 처리**되며(예: `GET /table-extractor/dbio/{그_ID}`), 재귀 중 만난 참조에만 적용된다 — `extract_from_module`이 `visited` 체크 바로 옆에서 `excluded`를 확인해 걸리면 소스를 읽지 않고 skip한다(dbio/biz/service/batch 타입 무관, ID 하나로 통일 체크). 테스트: `tests/tools/test_excludes.py`, `tests/tools/test_table_extractor.py`의 관련 케이스.

### 로깅
로거 이름은 `no_gada.<tool>` 계층(예: 공용 SQL 추출은 `no_gada.sql`). `main.py`에서 콘솔 + `RotatingFileHandler`(`logs/no_gada.log`, 5MB×5)를 붙이고, **루트=INFO, `no_gada`=DEBUG**로 설정해 서드파티 DEBUG 노이즈는 억제하고 앱 로그만 상세히 남긴다. `logs/`는 gitignore.
포맷은 `%(asctime)s %(levelname)s [%(name)s] (%(filename)s:%(lineno)d) %(message)s` — 발생 위치(`파일명:라인번호`)를 포함해 로그만 보고 코드 지점을 바로 찾을 수 있게 한다.

## 프로젝트 구조

```
app/
  main.py                     # FastAPI 앱 조립 + 로깅 설정
  common/text.py              # sanitize_text (툴 공용 텍스트 정제)
  common/sql.py               # extract_tables (툴 공용 Oracle 테이블 추출)
  common/proframe.py          # Module_Type/ResourceGroup (ProFrame ID 분류 체계, 툴 공용)
  common/dbio.py              # read_dbio_xml 등 (DBIO ID → 원격 XML 조회, 툴 공용)
  common/source.py            # SourceReader/SftpSourceReader/default_reader (원격 SFTP I/O, 툴 공용)
  common/db.py                # DbClient/MySqlDbClient/default_db (원격 DB 조회 I/O, 툴 공용)
  common/schema.py            # fetch_pk_columns (all_tables → 테이블별 PK 컬럼, 툴 공용)
  tools/sql_bench/router.py   # SQL 텍스트 → 테이블
  tools/table_extractor/router.py|service.py|mapper.py|migrate.py  # 라우터 / 오케스트레이션 / DBIO XML→SQL 파서 / 이관 SQL 생성(순수)
  static/
    index.html                # 사이드바 + 툴별 page 컨테이너
    js/app.js                 # nav 전환 + 공용 헬퍼
    css/ , tools/<tool>/      # 공용/툴별 스타일·스크립트
tests/
  common/test_text.py         # sanitize_text 단위 테스트
  common/test_sql.py          # extract_tables / strip_db_links 단위 테스트
  common/test_db.py           # db.py 단위 테스트 (default_db 팩토리 + fake client Protocol)
  common/test_schema.py       # fetch_pk_columns 단위 테스트 (fake db 주입)
  tools/test_sql_bench.py     # SQL Bench 회귀 케이스
  tools/test_table_extractor.py  # Table Extractor (dbio/mapper/라우터/pks/migrate-sql, fake reader·db 주입)
  tools/test_migrate.py       # 이관 SQL 생성 순수 함수(build_migration_sql: WHERE·제외·그룹핑)
remote_ap_server/                # 개발용 로컬 SFTP(atmoz/sftp) + 실물 DBIO 픽스처
remote_db_server/             # 개발용 로컬 MySQL(mysql:8.0) + all_tables 등 조회용 데이터(init/*.sql)
pyproject.toml                # name=no-gada, deps: fastapi/uvicorn/sqlglot/paramiko/PyMySQL
```

## 처리 범위 밖 (SQL Bench 한계 — README 상세)

순수 텍스트 파싱이라 DB에 접속하지 않는다. 따라서: **뷰와 물리 테이블을 구별 못 함**, 시노님 미해석, `SCOTT.EMP`·`HR.EMP`·`EMP@REMOTE`가 모두 `EMP` 하나로 뭉침(원본에서 스키마·DB링크 직접 확인 필요), PL/SQL·동적 SQL 미지원.

## 작업 원칙

- **회귀 우선**: 새 오추출/누락 사례가 나오면 먼저 `tests/`에 케이스를 추가하고 나서 `app/common/sql.py`를 고친다. 전체 회귀 케이스 사양은 `plan.md` 참고.
- 이름 관련: 코드 모듈명 `sql_bench`/`table_extractor`는 화면 이름 "SQL Bench"/"Table Extractor"와 매핑되며, 라우트 prefix·`data-page`·정적 디렉토리가 모두 이 이름으로 묶여 있으니 리네이밍 시 함께 바꿔야 한다.
