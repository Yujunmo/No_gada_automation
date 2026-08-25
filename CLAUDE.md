# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**No_Gada** — 반복 수작업("노가다")을 없애기 위한 **Oracle 전용** 사내 자동화 툴킷. 여러 도구를 좌측 사이드바로 전환하는 **단일 FastAPI 웹 서비스**다. 각 도구는 백엔드(`app/tools/<name>/`)와 프론트(`app/static/tools/<name>/`) 한 쌍으로 독립 구성된다.

| 도구 | 모듈 | 기능 | 상태 |
|------|------|------|------|
| **SQL Bench** | `sql_bench` | 붙여넣은 Oracle SQL → 참조 테이블 추출 | 구현됨 |
| **Table Extractor** | `table_extractor` | module_type(dbio/service/batch/biz)/resource_group/file_id → 원격지(SFTP) 소스 재귀 탐색 → 참조 테이블·PK·이관 SQL | 구현됨 |

사이드바에는 `Impact Analysis`도 "준비중"으로 자리만 잡혀 있다(영향도 분석 도구, 향후 추가 예정).

## 명령어

```bash
# 설치 (Python 3.9+)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 로컬 개발 env (python-dotenv가 app/main.py 기동 시 .env를 자동 로드)
cp .env.example .env

# 개발 서버 (http://localhost:8000)
uvicorn app.main:app --reload

# Table Extractor 수동 검증용 로컬 SFTP (회사 서버 대역, 127.0.0.1:2222 testuser/testpass)
(cd remote_ap_server && docker compose up -d)     # 정지: docker compose down

# 데이터 조회용 로컬 Oracle (기본값 대상 — 회사 실서버와 방언 일치, 127.0.0.1:1521 testuser/testpass, service_name=NOGADA)
pip install -e ".[oracle]"                         # oracledb 드라이버 (기본 설치에는 없음)
(cd remote_oracle_server && docker compose up -d)  # 정지: docker compose down / 초기화: down -v

# 데이터 조회용 로컬 MySQL (대안 리허설 — .env의 NOGADA_DB_DIALECT를 mysql+pymysql로 바꾸면 전환)
(cd remote_db_server && docker compose up -d)      # 정지: docker compose down / 초기화: down -v

# 전체 테스트 (pyproject에 -v 기본 적용, 현재 202개 수집)
pytest

# 단일 테스트 / 필터
pytest tests/tools/test_sql_bench.py::test_multiple_statements_supported
pytest -k dual
```

린터/타입체커는 설정돼 있지 않다(테스트만이 게이트). 단위/통합 테스트는 네트워크 없이 인메모리 fake reader/client로 돌므로 Docker 없이도 `pytest`가 통과한다 — Docker SFTP/DB는 브라우저/`curl` 수동 검증에만 필요.

## 아키텍처 (큰 그림)

### 멀티툴 플러그인 구조
`app/main.py`가 각 도구의 `router`를 `include_router`로 붙이고, 마지막에 `StaticFiles`를 `/`에 마운트한다. **정적 파일 마운트는 반드시 라우터 뒤**에 와야 API 경로가 가려지지 않는다. 각 도구 라우터는 자기 네임스페이스를 갖는다: `APIRouter(prefix="/sql-bench")` → `POST /sql-bench/extract`. `main.py`는 다른 어떤 import보다 먼저 `load_dotenv()`를 호출해 `.env`를 `os.environ`에 반영한다(아래 "환경변수(.env)" 참고).

### 새 도구 추가 레시피 (여러 파일에 걸침)
1. `app/tools/<name>/`에 `__init__.py`, `router.py`(`APIRouter(prefix="/<name>")`), 필요 시 `service.py`.
2. `app/main.py`에서 라우터 import + `include_router`.
3. `app/static/tools/<name>/`에 `<name>.js` / `<name>.css`.
4. `app/static/index.html`: 사이드바에 `<a data-page="<name>">` nav 항목 + `<div id="page-<name>">` 컨테이너 추가, `<head>`/하단에 css·js 링크 추가.

### 프론트엔드 규약 (프레임워크 없음, 순수 JS)
- `app/static/js/app.js`가 `.nav-item[data-page="X"]` 클릭 시 `#page-X` 컨테이너만 표시하고 나머지를 숨긴다. 공용 헬퍼 `App.showToast` / `App.copyToClipboard` 제공. 사이드바 접기/펼치기 상태는 `localStorage`에 유지.
- 각 도구 JS는 자기 `#page-<name>` 컨테이너를 찾아 `innerHTML`을 주입하고, 자기 엔드포인트(`/<name>/...`)로 `fetch`한다. 즉 **`data-page` 값 = 컨테이너 id 접미사 = 도구 이름**으로 세 곳이 묶여 있다.

### 테이블 추출 파이프라인 (`app/common/parse/sql.py`)
테이블 추출은 **공용 모듈**(`app/common/parse/sql.py`)에 있고 `sql_bench` 라우터와 `table_extractor`가 함께 import한다(도구 간 직접 의존 없음). 클래스가 아니라 상태 없는 모듈 함수 묶음이다.
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
툴 횡단 관심사를 3개 서브패키지로 나눠 둔다: **`io/`**(순수 I/O 어댑터), **`parse/`**(순수 텍스트·코드 파싱), **`proframe/`**(도메인 지식, `io/` 위에 얹힘). 파일명·import 경로만 봐도 소속 층이 드러난다.

**`parse/`** — 부작용 없는 순수 함수 (I/O 없음, 테스트 주입 불필요):
- `parse/text_sanitize.py`의 `sanitize_text(text) -> (cleaned, removed)`: 유니코드 카테고리 기준으로 `Cf`(제로폭·BOM·소프트하이픈·방향마크) 제거, `Zs`(NBSP·전각공백) → 일반 공백, 탭/개행은 보존. **멱등**이라 경계(라우터)에서 다시 호출해도 무해.
- `parse/sql.py`의 `extract_tables` / `ExtractionError`: Oracle SQL 테이블 추출(위 파이프라인 참고). `sql_bench`·`table_extractor` 공용.
- `parse/sql.py`의 `strip_db_links(sql) -> (cleaned, links)`: `@dblink` 텍스트 제거(문자열·주석 내부 `@` 보존). `extract_tables`가 파싱 전처리로 호출.
- `parse/c_source.py`의 `strip_comments(text) -> (cleaned, removed_count)`: C 소스에서 `//` 줄 주석 / `/* */` 블록 주석 제거(`removed`는 **제거한 주석 개수**, 목록이 아님). 문자열·문자 리터럴 내부의 `//` `/*`는 상태 기계로 보존, 주석 자리에는 개행을 남겨 원본 줄 번호 유지. `table_extractor.refs`가 콜 매크로 정규식 매칭 전에 사용(주석 처리된 죽은 코드에 실제 콜 매크로 형태가 남아 있어 오탐 방지).

**`io/`** — 순수 I/O 어댑터 (프로토콜 교체 지점, 테스트에서 fake로 대체):
- `io/sftp.py`의 `SourceReader`(Protocol) / `SftpSourceReader` / `SourceNotFound`·`SourceError` / `default_reader()`: 원격 소스 I/O 인프라(경로→내용 문자열). 회사 서버가 SFTP라 paramiko 기반. `default_reader()`는 env(`NOGADA_SFTP_HOST/_PORT/_USER/_PASS/_BASE`, 기본값 `remote_ap_server` 127.0.0.1:2222/testuser)에서 `SftpSourceReader`를 조립하는 팩토리. 라우터에 `Depends(default_reader)`로 주입 → 테스트에서 `app.dependency_overrides`로 인메모리 fake reader 교체 가능. 바이트→문자열 디코딩 인코딩은 `NOGADA_SOURCE_ENCODING`(기본 `utf-8`)로 지정 — 회사 서버가 UTF-8이 아니면(EUC-KR/CP949 등) 반입 시 이 값만 바꾸면 된다. `io/ssh.py`의 `default_command_runner()`(SSH 명령 실행 인프라, 같은 회사 서버·같은 `NOGADA_SFTP_*` 접속정보 공유)도 이 env를 그대로 쓴다. 이 프로그램이 로컬에 읽고 쓰는 텍스트 파일(`excludes.py`의 `config/excluded_refs.txt`·`excluded_tables.txt`, `module_source.py`의 `config/module_group_map.txt`, `main.py`의 `logs/no_gada.log`)도 같은 env를 따른다 — 회사 로컬 환경(텍스트 편집기 등)에서 이 파일들을 직접 열어볼 수 있어 인코딩을 일관되게 맞춰둔다.
- `io/db.py`의 `DbClient`(Protocol) / `SqlAlchemyDbClient` / `DbError`·`QueryError` / `default_db()`: 원격 DB I/O 인프라(SQL→결과 행 `list[dict]`). `io/sftp.py`와 쌍둥이 구조. **SQLAlchemy `Engine`(Core만 사용, ORM 아님) 기반이라 DB 종류가 바뀌면 `NOGADA_DB_DIALECT`(URL scheme) env만 바꾸면 되고 호출부 SQL은 그대로 유지**된다 — 방언별 paramstyle 차이를 SQLAlchemy가 흡수하므로 호출부는 항상 named bind(`:col`)로 SQL을 쓴다. `params`가 dict이고 값이 list/tuple이면 `bindparam(expanding=True)`로 `IN` 절을 자동 확장한다. `query`마다 접속/해제하는 상태 없는 모델(Engine 자체와 connection pool은 재사용), 결과는 dict 행 리스트, 읽기 전용(커밋 안 함). 접속 실패는 `DbError`, SQL 실행 실패는 `QueryError`. 라우터에 `Depends(default_db)`로 주입 → 테스트는 fake client로 교체. 소비처: `db_schema.fetch_pk_columns`(→ `table_extractor`의 `/pks`·`/migrate-sql`).
  - **기본값은 Oracle**(`_build_url_from_env()`): `NOGADA_DB_HOST`=127.0.0.1, `_PORT`=1521, `_USER`=testuser, `_PASS`=testpass, `_NAME`=NOGADA, `_DIALECT`=`oracle+oracledb` — 실제 반입 대상과 방언을 맞춘 기본값(`remote_oracle_server/`). MySQL 리허설(`remote_db_server/`)을 쓰려면 이 6개를 그쪽 값(host 동일/port 3306/name `nogada`/dialect `mysql+pymysql`)으로 바꾼다.
  - **dialect가 `oracle`로 시작하면 `NOGADA_DB_NAME`을 `service_name` 쿼리 파라미터로** 접속 URL에 넣는다(그 외 dialect는 `database=`). Oracle은 SID가 아니라 PDB `service_name`으로 접속해야 하며, `database=`로 넘기면 "SID ... is not registered with the listener"로 접속 실패 — `remote_oracle_server/`(gvenzl/oracle-free)로 실측 확인됨.

**`proframe/`** — ProFrame 도메인 지식 (`io/` 위에 얹힘, `__init__.py`가 `types.py`에서 재수출해 `from app.common.proframe import Module_Type` 형태 지원):
- `proframe/types.py`의 `Module_Type` / `ResourceGroup`(`Literal` 타입) / `PROFRAME_ROOT`: ProFrame ID 분류 체계(`dbio/service/batch/biz`, 업무그룹 `PCSP/PCSH/NCOM/NCSP/PCOM/PPFR/RLGR`). module_type 4종 전체에 걸친 값이라 공용에 둠 — `table_extractor`가 먼저 쓰지만 다른 툴(예: Impact Analysis)도 소비처가 될 예정.
- `proframe/dbio.py`의 `read_dbio_xml(file_id, reader) -> str` / `classify_sqltype(file_id) -> str` / `UnknownSqlType`: DBIO ID로 원격 XML을 읽는 범용 동작. 실물 파일이 `release/dbio/xml/<ID>.xml`로 **평면 배치**(`DBIO_RESOURCE_ROOT`)라 경로는 `{ROOT}/<ID>.xml` 1회 조합·조회로 끝난다. `classify_sqltype`(`SQL_TYPE_BY_SUFFIX`/`ID_SUFFIX_RE`, ID 끝 2글자 코드)로 **접미사가 인식 가능한 DBIO ID인지 검증**해 잘못된 ID를 파일없음(404)보다 명확한 400으로 먼저 거른다.
- `proframe/module_source.py`의 `read_module_source(...)` / `module_path(...)` / `build_group_map(...)` / `load_group_map(...)` / `write_group_map(...)` / `COMPILE_ROOT`: service/batch/biz 모듈 C 소스 위치 규칙 + 조회(`dbio.py`의 자매). 최상위 진입은 `resource_group`을 알고 있어 `module_path`로 직접 조합, 재귀 중 발견한 참조는 `resource_group` 불명이라 우선 `group_map`(사전 매핑) 조회 후 실패 시 `COMPILE_ROOT`를 listdir해 순차 탐색(find 폴백). `load_group_map()`은 env `NOGADA_MODULE_GROUP_MAP_PATH`(기본 `config/module_group_map.txt`)에서 로드. `build/write_group_map`은 오프라인 배치에서만 사용.
- `proframe/db_schema.py`의 `fetch_pk_columns(tables, db) -> {테이블: [PK컬럼]}`: `all_tables`(테이블→PK컬럼 매핑, 복합키는 여러 행)를 **1회 쿼리**로 조회해 테이블별 PK 컬럼을 돌려주는 딕셔너리 조회 도메인 로직. 입력을 대문자·중복 정규화하고 요청한 모든 테이블을 키로 포함(딕셔너리에 없으면 `[]`), 컬럼 순서는 DB 행 순서 보존. `io/db.py` 위에 얹힌 층. table_extractor의 `/pks`·`/migrate-sql`이 사용.

### 환경변수(`.env`)
`python-dotenv`가 core dependency이고, `app/main.py`가 다른 어떤 것보다 먼저 `load_dotenv()`를 호출해 `.env`(레포 루트)를 `os.environ`에 반영한다. 이미 export된 OS 환경변수는 `.env` 값보다 우선한다(`load_dotenv()` 기본 `override=False`). 템플릿은 `.env.example`(커밋됨) — `cp .env.example .env`로 시작. 대상 15개 변수: `NOGADA_DB_*`(6, 위 `io/db.py` 참고 — 템플릿은 MySQL 블록이 활성화·Oracle 블록은 주석으로 나란히 제공), `NOGADA_SFTP_*`(5, `io/sftp.py`) + `NOGADA_SOURCE_ENCODING`(SFTP/SSH 공용 디코딩 인코딩, 기본 `utf-8`), `NOGADA_EXCLUDED_REFS_PATH`/`NOGADA_MODULE_GROUP_MAP_PATH`/`NOGADA_EXCLUDED_TABLES_PATH`(경로 오버라이드 3종, 기본값 그대로면 생략 가능). **주의**: 코드의 하드코딩 기본값(`_build_url_from_env()`)은 Oracle이지만 `.env.example`의 활성 블록은 MySQL이 먼저 온다 — `.env`를 만들지 않고 그냥 실행하면 Oracle 기본값으로, `.env.example`을 그대로 복사하면 MySQL로 붙는다는 차이를 인지할 것.

### Table Extractor 파이프라인
`sql_bench`가 SQL 텍스트를 직접 받는 반면, `table_extractor`는 **식별자(module_type/(resource_group)/file_id)로 원격 파일을 찾아 읽은 뒤** 그 안팎의 SQL/참조를 재귀적으로 추적해 테이블을 추출한다. REST 계약은 부작용 없는 조회라 경로 파라미터 GET(바디 없음)이며, **`resource_group`은 옵셔널**이다 — 같은 핸들러에 라우트 2개를 붙여 **DBIO는 `GET /table-extractor/{module_type}/{file_id}`(2세그먼트, resource_group 생략)**, **그 외(Service/Batch/Biz)는 `GET /table-extractor/{module_type}/{resource_group}/{file_id}`(3세그먼트, 필수)**로 받는다. DBIO는 resource_group을 파일 경로에 쓰지 않아 생략 가능(3세그먼트로 줘도 하위호환 동작, 값은 무시). 프론트는 module_type이 dbio면 세그먼트를 빼고 콤보박스도 숨긴다. `module_type`/`resource_group`은 `Literal`(공용 `proframe/types.py`)이라 잘못된 값은 FastAPI가 422로 자동 거부.

흐름: `router.py`(`Depends(default_reader)`로 SFTP reader 주입) → `service.extract(module_type, resource_group, file_id, reader)`가 두 갈래로 디스패치:

**1) DBIO(리프)** — `extract_from_dbio`:
1. `dbio.read_dbio_xml`(공용): ID 접미사 검증(`classify_sqltype`) → `release/dbio/xml/<ID>.xml` 조회. 인식 못 하는 접미사는 `UnknownSqlType`(→400).
2. `dbio_sql.extract_sql`(table_extractor 전용): ProFrame published XML에서 `<sqlString>` 텍스트 수집(루트 태그/네임스페이스 무관, 로컬네임 매칭, XML 파싱 실패 시 정규식 폴백). 바인드는 이미 Oracle `:name`이라 치환 없음.
3. 각 SQL을 `extract_tables`로 돌려 테이블 합집합. `dbios=[file_id]`(자기 자신 self-inclusion).

**2) Service/Batch/Biz(재귀 DFS)** — `extract_from_module(module_type, resource_group, file_id, reader, visited, excluded, group_map)`:
1. 최상위 호출(`visited=None`)에서 `excluded`(`load_excluded_refs()`)·`group_map`(`load_group_map()`)을 1회 로드해 재귀 전체에 그대로 전달. `visited`(공유 set)로 순환 참조·중복 재방문을 차단(타입 무관, ID 하나로 통일 체크).
2. `read_module_source`로 소스 조회 — 최상위 호출의 실패는 그대로 전파(→라우터 404/503), 재귀 중 발견된 참조의 실패는 skip+warn 후 부분성공.
3. 소스를 성공적으로 읽으면 **자기 자신을 `services`/`bizs`에 self-include**(module_type이 service/biz일 때만 — DBIO의 `dbios=[file_id]`와 동일 규칙).
4. `refs.scan_module_refs`(정규식 기반, `strip_comments`로 죽은 코드 오탐 방지 후 매칭)로 `(ref_type, ref_id)` 목록을 얻어 각각 처리:
   - 이미 `visited` → skip. `excluded`에 있으면 `visited`에만 추가하고 skip(소스 안 읽음).
   - `batch`: 소스를 들여다보지 않고 `batches`에 ID만 기록(배치는 별도 잡 호출이라 재귀 안 함).
   - `dbio`: `extract_from_dbio` 호출, 실패(`SourceNotFound`/`SourceError`/`UnknownSqlType`/`ExtractionError`)는 skip.
   - `service`/`biz`: `resource_group=None`으로 재귀 호출(업무그룹 불명 → `read_module_source`의 group_map/find 폴백으로 알아서 찾음).
5. 하위 결과의 `tables`/`sql`/`dbios`/`batches`/`services`/`bizs`를 전부 부모로 merge(union) — 트리를 타고 올라가며 누적.

응답(`ExtractResponse`): `{tables, sql, dbios, batches, services, bizs}` — `tables`/`batches`/`services`/`bizs`는 정렬된 리스트, `dbios`는 발견 순서 보존, `sql`은 수집한 SQL을 `;`로 이어붙인 문자열.

에러 매핑(라우터 `extract`): 빈 ID→400, `module_type != dbio`인데 `resource_group` 없음→400, `UnknownSqlType`/`ExtractionError`→400, `SourceNotFound`→404, `SourceError`→503.

**`POST /table-extractor/{module_type}/extract-batch`**(여러 ID 동시 추출): `{resource_group?, file_ids:[...]}` →
`{tables, sql, dbios, batches, services, bizs, succeeded, failed:[{file_id,error}]}`. 프론트가 이제
항상 이 엔드포인트만 호출한다(ID 1개여도 동일 경로) — 위 단일 GET 라우트는 계약을 그대로 유지하되
UI에서 더 이상 직접 호출하지 않는다. 경로에 "batch"가 아니라 "extract-batch"를 쓴 이유는
`module_type == "batch"`(ProFrame 배치 모듈)와 어휘가 겹치는 `POST /table-extractor/batch/batch` 같은
혼란을 피하기 위함. 상한 `MAX_BATCH_FILE_IDS=50`(초과 시 400 — SFTP 재귀 탐색이 ID마다 새로 도는
구조라 너무 많으면 느려짐). `service.extract_batch`가 각 ID마다 기존 `extract()`를 **독립적으로**
(각자 `visited=None`) 호출해 성공은 UNION 병합, 실패는 개별 `FailedItem(file_id, error)`으로 기록한다
— **부분성공**: 일부 ID가 404/파싱실패 등으로 실패해도 요청 전체는 200이고, `failed`에 사유와 함께
담긴다(전부 실패해도 200). `excluded_tables` 필터는 `extract()` 내부에서 항목별로 이미 적용되므로
병합 후 재필터링하지 않는다(`filter(A)∪filter(B) == filter(A∪B)`). **`dbios`는 항목 간에 중복될 수
있다**(각 항목이 독립된 `visited`라 순환 차단이 항목 간에는 보장되지 않음 — 재귀 트리 하나 안에서는
`visited`가 중복을 막아주지만, 서로 다른 top-level 항목이 같은 하위 DBIO를 각자 발견할 수 있음) —
`extract_batch`가 별도 seen 집합으로 최초 등장 순서를 유지하며 dedupe한다. 라우터는 요청 형태
자체가 잘못된 경우만 400으로 거부한다(빈 `file_ids`, 상한 초과, 비-dbio인데 `resource_group` 누락).

**`POST /table-extractor/pks`**: `{tables:[...]}` → `{pks:{테이블:[PK컬럼]}}`. 추출과 분리된 조회로, 프론트가 추출 직후 전체 테이블 목록으로 1회 호출해 캐시하고 선택 변경 시 **PK 합집합**을 클라이언트에서 계산한다. `Depends(default_db)`로 DB 주입, `db_schema.fetch_pk_columns` 호출. 에러 매핑: `DbError`→503, `QueryError`→500. 프론트(`table_extractor.js`): **필터된(보이는) 테이블 목록이 곧 이관 대상**(별도 선택 체크박스 없음 — 텍스트/접두사 필터·삭제로 좁힘). 이관 sql 위 키 입력란은 그 대상들의 **PK 합집합**(중복 제거·첫 등장 순서)을 실시간 표시.
- **일반 PK / 날짜 PK 박스 분리**: PK 합집합을 `isDateColumn`(컬럼명이 `date`로 끝나는지) 기준으로 나눠 **위(일반 PK) / 아래(날짜 PK) 두 개의 독립된 박스**(`.te-keyin-box`, 각자 `max-height`+`overflow-y:auto`로 자체 스크롤)에 렌더한다. 어느 한쪽이 비면 그 박스는 렌더 자체를 생략.
- **일반 PK 우선순위 정렬**: `sortByPkPriority`가 `PK_PRIORITY = ['mncm_code','fund_code','cmpn_code','itms_code']`(대소문자 무관 매칭)에 해당하는 컬럼을 그 순서로 먼저 배치하고, 나머지는 안정 정렬로 기존 등장 순서를 유지한다.
- **날짜 PK**: 컬럼명이 `date`로 끝나면(사내 관행) 날짜 필드로 보고 **[단일|기간] 토글** 제공(YYYYMMDD 8자리). 입력 상태는 `keyinState`(컬럼별 `{isDate,mode,value|single|from|to}`)에 보존돼 필터·재렌더에도 유지.
- **이관 SQL 생성**: 'FROM 링크(원격 소스)' + 'TO 링크(대상)' 입력 + '이관 SQL 생성' 버튼 → 프론트는 `keyinState`를 컬럼별 조건(`eq`/`between`)으로 변환해 **`POST /table-extractor/migrate-sql`** 호출, 응답을 **팝업(모달)** 으로 표시. 각 테이블은 **자기 PK 컬럼만**(all_tables 조회) AND 결합, 값은 전부 문자열 따옴표(`''` 이스케이프), 단일=`=`/기간=`BETWEEN`. 값 미입력 컬럼은 조건절에서 제외(주석 표기), 한 테이블 키가 전부 비면 전체삭제 방지로 제외, PK없음 테이블 제외, COMMIT 없음.
- **팝업 그룹 박스**: 생성 SQL을 **테이블 접미사별 박스**로 나눠 담는다 — `_BS`/`_HT`/`_MA`/`_SM`/`_TR` 순(`migrate.GROUP_ORDER`), 그 외는 `기타`(비어 있는 그룹 생략). 박스마다 개별 복사 + 모달 '전체 복사'. **이관 SQL이 생성되지 않은 테이블**(PK없음 `no_pk` + 키 미매칭 `skipped`)은 모달 하단 **표**(1열 테이블명 / 2열 사유)로 표시. 모달은 X/배경클릭/Esc로 닫힘.

**`POST /table-extractor/migrate-sql`**: `{tables, from_link, to_link, keys:{컬럼:{op,value|start,end}}}` → `{sql, generated, skipped, no_pk, groups:[{key,sql,tables}]}`. 생성 형태는 `DELETE FROM t@<TO> WHERE ...` + `INSERT INTO t@<TO> SELECT * FROM t@<FROM> WHERE ...`(FROM=원격 소스에서 읽어 TO=대상에 넣음, TO 비우면 로컬, 링크 앞 `@` 중복 제거). 계층: **라우터**(요청 검증, `KeyCondIn`→`migrate.KeyCond` 변환, 에러 매핑) → **`service.migrate_sql`**(테이블명 대문자 정규화 + `db_schema.fetch_pk_columns`로 PK 조회 + 순수 함수 호출) → **순수 함수 `migrate.build_migration_sql`**(DB·HTTP 비의존, 그룹핑 포함, `tests/tools/test_migrate.py`로 고정).

프론트(`table_extractor.js`): `#te-id-input`은 쉼표로 여러 ID를 받는 텍스트 입력(`parseIds`가 공백
제거·중복 제거·순서 보존해 파싱, 클라이언트에서도 50개 상한 확인). `#te-submit` 클릭 → 항상
`POST /table-extractor/{type}/extract-batch` 호출(ID 1개여도 동일 경로) → **좌측 패널** = 테이블
목록(실시간 텍스트 필터 + `TRU/PFO/PTN/RPT` 접두사 필터 + 개별 삭제 + 전체/개별 복사, `FEP` 접두사는
이관 미지원이라 하단에 읽기 전용 분리), 그 아래 **"발견된 batch"** 섹션(있을 때만), 그 아래
**"일부 항목 조회 실패"** 섹션(`failed`가 있을 때만 — `renderFailedSection`이 이관 SQL 모달의
`.te-nogen-table`을 그대로 재사용해 `{ID,사유}` 2열 표로 표시), 그 아래 **"추출경로"** 섹션 —
`dbios`/`services`/`bizs`를 각각 접힌 토글 그룹으로 표시(클릭하면 펼쳐짐, 기본은 접힌 상태).
성공 결과가 하나도 없는데 `failed`만 있으면(전부 실패) `showAllFailed`가 빈 상태 메시지 + 실패
표를 같이 그린다. **우측 패널** = PK 키 입력 + 이관 SQL 생성(위 `/pks`·`/migrate-sql` 항목 참고).
업무그룹 입력은 7개 값(`ResourceGroup`)을 필터링하는 검색형 콤보박스.

### 설정 팝업 — "항상 제외" 목록 2종 (모듈 예외처리 / 테이블 추출 예외처리)
`excludes.py`가 형식이 동일한 설정 파일 2개를 조회+저장 둘 다 지원한다(`_write_names` 공용 저장 로직). 정규화 방식만 다르다 — ID는 재귀 매칭이 대소문자 구분이라 원형 보존, 테이블명은 시스템 전체가 대문자 규약이라 대문자화. 파일은 `NOGADA_SOURCE_ENCODING`을 따른다(위 `io/` 참고).

1. **재귀 참조 제외**(`load_excluded_refs`/`save_excluded_refs`): `service.extract_from_module`이 재귀 중 "참조로 만나는" DBIO/모듈 ID를 skip시킨다(소스를 읽지 않고 `visited`에만 추가). `config/excluded_refs.txt`(한 줄에 ID 하나, `#` 주석, 경로는 `NOGADA_EXCLUDED_REFS_PATH`로 override). **최상위로 직접 요청한 ID는 이 목록과 무관하게 항상 처리**되며, 재귀 중 만난 참조에만 적용된다. `GET`/`POST /table-extractor/excluded-refs`(`{ids:[...]}`)로 조회/저장(전체 교체).
2. **테이블 추출 예외**(`load_excluded_tables`/`save_excluded_tables`): `service.extract()`가 `extract_from_dbio`/`extract_from_module` 결과를 반환하기 **직전**에 최종 `tables` 목록만 걸러낸다(`dbios`/`services`/`bizs` 등 추출근거 트레이스는 그대로 둠 — 재귀 로직 자체는 건드리지 않는 순수 후처리). `config/excluded_tables.txt`(경로는 `NOGADA_EXCLUDED_TABLES_PATH`). `GET`/`POST /table-extractor/excluded-tables`(`{tables:[...]}`)로 조회/저장.

프론트(`table_extractor.js`): 컨트롤 바의 `⋮`(`#te-settings-btn`) 클릭 → 좌측 사이드 네비(`#te-settings-nav`) + 우측 패널(`#te-settings-panel`) 구조의 설정 모달(`#te-settings-modal`, 기존 `#te-modal`과 별개)이 열린다. 네비 항목("테이블 추출 예외처리"/"모듈 예외처리")은 각각 `makeListSettingsPanel(opts)` 팩토리로 만든 동일한 조회→편집→저장 UI를 쓴다 — `opts`로 endpoint/request·response 필드명(`tables` vs `ids`)/정규화 함수(대문자화 여부)/라벨·설명 문구만 다르게 주입. 새 탭을 추가하려면 네비 버튼 + `SETTINGS_PANELS`에 팩토리 호출 한 줄만 더하면 된다.
- **조회→편집→저장 흐름**: 패널을 열 때마다 `GET`으로 서버의 현재 확정 목록(`committed`)을 받아 작업 사본(`draft`)을 초기화한다. 추가/삭제는 `draft`에만 반영되고(입력 후 Enter 또는 추가 버튼), **저장** 버튼을 눌러야 `POST`로 전체 교체 저장되며 그 응답이 새 `committed`가 된다. 미저장 변경이 있으면 "저장되지 않은 변경사항이 있습니다" 힌트가 뜨고 저장 버튼이 활성화되며, 팝업을 저장 없이 닫고 다시 열면 항상 최신 서버 상태로 재초기화되어 미저장 편집은 버려진다.

### 로깅
로거 이름은 `no_gada.<tool>` 계층(예: 공용 SQL 추출은 `no_gada.sql`). `main.py`에서 콘솔 + `RotatingFileHandler`(`logs/no_gada.log`, 5MB×5)를 붙이고, **루트=INFO, `no_gada`=DEBUG**로 설정해 서드파티 DEBUG 노이즈는 억제하고 앱 로그만 상세히 남긴다. `logs/`는 gitignore.
포맷은 `%(asctime)s %(levelname)s [%(name)s] (%(filename)s:%(lineno)d) %(message)s` — 발생 위치(`파일명:라인번호`)를 포함해 로그만 보고 코드 지점을 바로 찾을 수 있게 한다.

## 프로젝트 구조

```
app/
  main.py                     # FastAPI 앱 조립 + load_dotenv() + 로깅 설정
  common/                     # 툴 공용 (3개 서브패키지로 층 분리)
    io/sftp.py                #   SourceReader/SftpSourceReader/default_reader (원격 SFTP I/O)
    io/ssh.py                 #   SshCommandRunner/default_command_runner (원격 SSH 명령 실행 I/O, io/sftp와 같은 서버·NOGADA_SFTP_*·NOGADA_SOURCE_ENCODING 공유)
    io/db.py                  #   DbClient/SqlAlchemyDbClient/default_db (원격 DB 조회 I/O, SQLAlchemy Engine, 기본 Oracle)
    parse/text_sanitize.py    #   sanitize_text (유니코드 정제, 순수)
    parse/sql.py              #   extract_tables/strip_db_links (Oracle SQL 파싱, 순수)
    parse/c_source.py         #   strip_comments (C 소스 주석 제거, 순수)
    proframe/__init__.py      #   types 재수출 (from app.common.proframe import Module_Type)
    proframe/types.py         #   Module_Type/ResourceGroup/PROFRAME_ROOT (ProFrame ID 분류 체계)
    proframe/dbio.py          #   read_dbio_xml 등 (DBIO ID → 원격 XML 조회, io/sftp 위)
    proframe/module_source.py #   read_module_source 등 (service/batch/biz 모듈 C 소스 조회, io/sftp 위)
    proframe/db_schema.py     #   fetch_pk_columns (all_tables → 테이블별 PK 컬럼, io/db 위)
  tools/sql_bench/router.py   # SQL 텍스트 → 테이블
  tools/table_extractor/
    router.py                 #   라우터, HTTP 상태 매핑
    service.py                 #   ExtractResult, extract()/extract_from_dbio()/extract_from_module()(재귀 DFS)/migrate_sql()
    dbio_sql.py                 #   DBIO published XML → <sqlString> 추출
    refs.py                     #   C 소스 → (type, id) 참조 스캔 (정규식 기반: dbio/biz/service/batch)
    excludes.py                 #   config/excluded_refs.txt·excluded_tables.txt 조회+저장 ("항상 제외" 목록 2종, 설정 팝업이 사용)
    migrate.py                  #   이관 SQL 생성(순수)
  static/
    index.html                # 사이드바 + 툴별 page 컨테이너
    js/app.js                 # nav 전환 + 공용 헬퍼
    css/ , tools/<tool>/      # 공용/툴별 스타일·스크립트
tests/
  common/test_text_sanitize.py  # sanitize_text 단위 테스트
  common/test_sql.py          # extract_tables / strip_db_links 단위 테스트
  common/test_csource.py      # strip_comments 단위 테스트
  common/test_db.py           # db.py 단위 테스트 (default_db 팩토리 + dialect 전환 + fake client Protocol)
  common/test_schema.py       # fetch_pk_columns 단위 테스트 (fake db 주입)
  common/test_module_src.py   # read_module_source / group_map 단위 테스트
  common/test_sftp.py         # default_reader() 팩토리의 env(NOGADA_SFTP_*/_SOURCE_ENCODING) 반영 단위 테스트(네트워크 없음)
  common/test_ssh.py          # default_command_runner() 팩토리의 env 반영 단위 테스트(네트워크 없음)
  tools/test_sql_bench.py     # SQL Bench 회귀 케이스
  tools/test_table_extractor.py  # Table Extractor (dbio/재귀/라우터/pks/migrate-sql/excluded-tables/excluded-refs, fake reader·db 주입)
  tools/test_migrate.py       # 이관 SQL 생성 순수 함수(build_migration_sql: WHERE·제외·그룹핑)
  tools/test_excludes.py      # load/save_excluded_refs·load/save_excluded_tables 단위 테스트(인코딩 전환 포함)
  tools/test_refs.py          # scan_module_refs 단위 테스트
config/
  excluded_refs.txt           # NOGADA_EXCLUDED_REFS_PATH 기본 경로(재귀 참조 제외, 설정 팝업 "모듈 예외처리" 탭이 저장)
  excluded_tables.txt         # NOGADA_EXCLUDED_TABLES_PATH 기본 경로(추출 결과 테이블 제외, 설정 팝업 "테이블 추출 예외처리" 탭이 저장, 최초 저장 전엔 파일 없음)
  module_group_map.txt        # NOGADA_MODULE_GROUP_MAP_PATH 기본 경로
.env.example                  # NOGADA_* env 템플릿 (python-dotenv가 실제 .env를 자동 로드)
remote_ap_server/             # 개발용 로컬 SFTP + 실물 DBIO/모듈 소스 픽스처, 127.0.0.1:2222
remote_db_server/             # 개발용 로컬 MySQL(mysql:8.0), 127.0.0.1:3306, all_tables 시드
remote_oracle_server/         # 개발용 로컬 Oracle(gvenzl/oracle-free), 127.0.0.1:1521, all_tables 동일 시드(기본 대상)
pyproject.toml                # name=no-gada, deps: fastapi/uvicorn/sqlglot/paramiko/SQLAlchemy/PyMySQL/python-dotenv, optional: dev/oracle(oracledb)
```
