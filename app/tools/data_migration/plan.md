# Table Extractor — 백엔드 (원격 소스 → 참조 테이블 추출)

> **기준:** DBIO 포맷·경로는 실물 픽스처 `remote_ap_server/files/…/release/dbio/xml/`(평면 `<ID>.xml`)를 정답으로 삼는다. *(2026-08-10 실물 경로 정정 — 이전 `publish_ecams/resource/<PROG>/<SQLTYPE>/…`는 오경로였음. Part 1의 날짜 로그 내 옛 경로 서술보다 2026-08-10 섹션이 최신이고, Part 2(재귀 추출)가 그보다도 더 최신이다.)*
>
> **모듈 경로 안내:** 이 문서 전체의 `app/common/*.py`(예: `source.py`, `dbio.py`, `sql.py`, `csource.py`, `module_src.py`, `proframe.py`) 언급은 전부 리펙터링(`450b9dd 1차 리펙터링 : 공통기능 재분류`) **이전** 플랫 구조 기준이다. 현재는 `app/common/io/`(`source.py`→`sftp.py`, `db.py`), `app/common/parse/`(`sql.py`, `text_sanitize.py`, `c_source.py`), `app/common/proframe/`(`proframe.py`→`types.py`, `dbio.py`, `module_source.py`, `db_schema.py`)로 재분류돼 있다(예: `module_src.py`→`proframe/module_source.py`). 현재 파일 분류는 `CLAUDE.md`의 "공용 모듈 `app/common/`" 섹션 참고. 이 문서의 `app/tools/table_extractor/mapper.py` 언급도 이후 **`dbio_sql.py`로 리네임**됐다(같은 파이프라인 층인 `refs.py`와 이름 축을 맞추기 위함 — "무엇처럼 생겼는지"가 아니라 "무엇을 다루는지"로 통일).

이 문서는 두 파트로 구성된다: **Part 1**은 DBIO 단일 경로의 최초 설계와 구현 진행 로그(2026-08-04~08-10), **Part 2**는 그 위에 이어진 Service/Batch/Biz 재귀 추출 확장(2026-08-13~08-16, 구현 완료)이다. Part 2가 Part 1의 범위를 포함해 최신화하므로, 둘이 상충하면 **Part 2가 최신**이다.

---

# Part 1 — DBIO 파이프라인 (최초 설계 + 진행 로그, 2026-08-04~08-10)

## Context
프론트(드롭박스+입력+버튼, 좌 테이블목록/우 SQL 패널)는 완성됐고 `추출하기` 버튼은 아직 무동작이다. 백엔드는 빈 스텁(`router.py`는 prefix만, `service.py`는 비어 있음)이다. 이번 작업은 **ID → 원격 소스 파일 → 참조 테이블** 파이프라인을 구현한다.

동작: 사용자가 타입(DBIO/Service/Batch/Biz)과 ID를 주면,
- **DBIO**: 해당 XML 매퍼 파일을 읽어 SQL을 꺼내 바로 테이블 추출.
- **Service/Batch/Biz**: 파일 안에 리터럴로 등장하는 하위 ID들을 스캔 → 타입 접두사로 분류 → **재귀** 해석(비-DBIO는 더 파고들고, DBIO에서 종료) → 모든 DBIO의 SQL에서 테이블 추출.

### 확정된 설계 입력
- DBIO 파일 = **ProFrame published XML**. 루트는 SQL타입별로 다르다: `<dynamicSqlQuery>`(DYNAMICSQL) · `<execSqlQuery>`(EXECSQL) 등. **SQL은 `<sqlString>` 엘리먼트의 텍스트**에 담긴다. `<execType>`(SELECT/INSERT…)·`<tableName>`·`<columnSet>`도 함께 있음.
- 상위 파일의 DBIO 참조 = **리터럴 ID 문자열**. 정규식 스캔.
- **재귀 중첩 가능** (Service→Biz→DBIO 등) → 방문 집합으로 순환 방지.
- DBIO id는 접두사가 없다(실물 예: `PFO_STCK_MA_DS200`, `PFO_MNCM_CLCD_HT_EI901`). 타입/경로는 **접미 패턴 + 소속 디렉토리**로 결정 → 아래 경로 규칙 참고. Service/Batch/Biz 규칙은 상위 `.c` 실물로 확정 필요.
- 바인드 변수는 Oracle `:name` 표기. 정규화는 **XML 언이스케이프만**(`&lt;`,`&gt;`,`&amp;`, CDATA). 동적 SQL 태그는 published 형태엔 사실상 없음(평문 SQL, 힌트/한글주석/UNION ALL/서브쿼리/listagg는 `extract_tables`가 이미 처리).
- FTP는 **지금 추상화만**, 실제 접속은 후속 PR. 로컬 샘플/테스트로 전 구간 검증.
- 출력 = **테이블 평면 합집합** `{tables, sql}` (+ 참고용 `dbios`).

## 재사용 자산
- `app/common/sql.py`의 **`extract_tables(sql) -> list[str]`** / `ExtractionError` — DBIO SQL에서 테이블 뽑는 핵심. 새 파싱 로직 만들지 않는다. (다중문장·CTE·DUAL·딕셔너리뷰·dblink 제외 전부 처리됨)
- 라우터 형태는 `app/tools/sql_bench/router.py` 패턴 그대로: Pydantic req/resp, `response_model`, `ExtractionError`→400, 로거 `no_gada.table_extractor`(자동으로 DEBUG+핸들러 상속).
- 앱 배선은 이미 완료(`main.py`에 `table_extractor_router` 마운트됨).

## 구현 (신규 파일 중심)

### 1. `app/common/source.py` — 소스 접근 추상화 (구현 완료)
```python
class SourceReader(Protocol):
    def read(self, path: str) -> str: ...          # 없으면 SourceNotFound, 접근실패 SourceError

class SftpSourceReader:                             # paramiko 기반 (개발/운영 공용)
    def __init__(self, host, *, port=22, user, password=None, base_dir="", ...): ...
    def read(self, path): ...                       # connect→open_sftp→read→decode; 부재→SourceNotFound

class SourceNotFound(Exception): ...
class SourceError(Exception): ...                  # 접속/인증/전송 실패
```
- FTP 미접속이라도 `LocalSourceReader`로 파이프라인 전체가 돈다. 서비스는 reader를 **주입**받아 테스트에서 fake 교체 가능.

### 2. `app/tools/table_extractor/ids.py` — 타입·경로 규칙 (설정 한 곳)
**실물 디렉토리 레이아웃**(`remote_ap_server/files/truap01dap1/proframe/proframe5.0/` 기준):
- DBIO(=SQL 리소스): `publish_ecams/resource/<PROG>/<SQLTYPE>/<ID>/<ID>.xml`
  - `<PROG>` = 프로그램/리소스그룹: `PCSP PCSH NCOM NCSP PCOM PPFR RLGR`
  - `<SQLTYPE>` = `DYNAMICSQL EXECSQL PERSIST VIEW` (모두 DBIO, 루트 태그만 다름)
  - 예: `PCSP/DYNAMICSQL/PFO_STCK_MA_DS200/PFO_STCK_MA_DS200.xml`, `PCSH/EXECSQL/PFO_MNCM_CLCD_HT_EI901/PFO_MNCM_CLCD_HT_EI901.xml`
- Service/Batch/Biz(=원본 C): `compile/<PROG>/src/{batch,module,serviceModule}/…/<ID>.c` (상위 `.c` 실물로 규칙 확정 필요)

```python
def resolve_path(id_type, id, reader) -> str
#   ★ id 하나로 경로가 결정되지 않음: <PROG>·<SQLTYPE>가 id에 인코딩돼 있지 않다.
#   DBIO는 resource 트리에서 **<ID>/<ID>.xml 를 탐색**(reader.list/glob)해 첫 매칭 사용.
#   (또는 요청에 PROG를 함께 받는 방안 — 상위 .c 스캔 규칙 확정 시 재검토)
def classify(id) -> str | None            # 접미/네이밍 패턴으로 타입 판별
def scan_ref_ids(text) -> list[str]       # 상위 소스에서 하위 ID 리터럴 정규식 수집(중복제거·등장순)
```
※ `classify`/`scan_ref_ids`의 정확한 정규식은 상위 `.c`에서 DBIO/하위ID가 박히는 실제 모습으로 확정.

### 3. `app/tools/table_extractor/mapper.py` — ProFrame DBIO XML → SQL 문자열들
```python
def extract_sql(xml_text) -> list[str]
```
- `xml.etree.ElementTree`로 파싱 → **`sqlString` 엘리먼트의 텍스트**를 수집(루트 태그 `dynamicSqlQuery`/`execSqlQuery` 등 무관, 자식은 `xmlns=""` 로컬네임스페이스). 보통 파일당 1개.
  - 구현 팁: 로컬네임 매칭 `for el in root.iter() if el.tag.split('}')[-1] == "sqlString"` (기본 네임스페이스 접두 무시). `el.text`가 이미 SQL 원문(ET가 `&lt;` 등 엔티티는 자동 언이스케이프).
- 정규화: **바인드 치환 불필요**(실물이 이미 Oracle `:name`). CDATA/엔티티 해제만(ET가 대부분 처리). → 사실상 `<sqlString>` 텍스트를 그대로 `extract_tables`에 넘기면 됨.
- XML 파싱 실패 시 폴백: `<sqlString ...>(.*?)</sqlString>` 정규식으로 블록 추출 후 엔티티 언이스케이프.

### 4. `app/tools/table_extractor/service.py` — 오케스트레이션
```python
def extract(id_type, id, reader) -> Result   # Result = (tables: list[str], sql: str, dbios: list[str])
```
- 내부 재귀 `_collect(id_type, id, reader, visited) -> (sqls, dbio_ids)`:
  - `id in visited`면 즉시 반환(순환 차단), 아니면 visited 추가.
  - `path=resolve_path(id_type, id, reader)`(DBIO는 트리 탐색으로 `<ID>/<ID>.xml` 위치 결정); `text=reader.read(path)`.
    - ※ 트리 탐색을 위해 `SourceReader`에 **디렉토리 나열용 메서드(예: `list(prefix)`/`glob`)** 추가 필요(현재는 `read`만). FTP/로컬 fake 양쪽에 구현.
  - `dbio`면 `mapper.extract_sql(text)` 반환(+ 이 id를 dbio 목록에).
  - 아니면 `scan_ref_ids(text)` → 각 ref를 `classify`로 타입 판별 → **재귀**로 누적. (접두사 매칭 안 되는 문자열은 무시)
- 수집된 각 SQL을 `extract_tables`로 돌려 **합집합**(정렬). DBIO별 파싱 실패는 `logger.warning` 후 **건너뜀**(부분 성공 허용). `sql`은 수집 SQL을 `;`로 이어 붙여 우측 패널 표시용으로 반환.

### 5. `app/tools/table_extractor/router.py` — 엔드포인트
```python
class ExtractRequest(BaseModel):  id_type: Literal["dbio","service","batch","biz"];  id: str
class ExtractResponse(BaseModel): tables: list[str];  sql: str;  dbios: list[str]

@router.post("/extract", response_model=ExtractResponse)
```
- 빈 `id` → 400. `SourceNotFound` → 404. 최상위 파일에서 아무 것도 못 얻거나 파싱 실패 → 400(`detail`). 로깅은 sql_bench와 동형(수신/완료 info, 실패 warning).
- reader는 env(`NOGADA_SFTP_*`)에서 `SftpSourceReader`로 생성(기본 `remote_ap_server` Docker SFTP 127.0.0.1:2222). 교체 지점 한 곳. → `app/common/source.py`의 `default_reader()`.

### 6. 프론트 연결 (마무리) `app/static/tools/table_extractor/table_extractor.js`
- `#te-submit` 클릭 → `POST /table-extractor/extract {id_type, id}` fetch.
- 성공: 좌측 `.te-empty`를 **테이블 목록**(sql_bench의 `.table-list`/`.table-item` 톤 재사용, 단 table_extractor 자체 스타일)으로 교체, 우측 `#te-sql` textarea에 `sql` 채움.
- 실패: 좌측에 에러 박스(components.css `.error-box`) 표시. 로딩 스피너 재사용.

## 명시적으로 남기는 결정
- **부분 성공**: Service/Batch/Biz 해석 중 개별 DBIO 파싱 실패는 스킵+경고, 나머지 합집합은 반환. 최상위 파일 자체 실패만 4xx.
- XML 매퍼 파서는 table_extractor 전용(현재 유일 사용처)이라 `app/common/`으로 올리지 않는다. 테이블 추출(`extract_tables`)만 공용 재사용.

## 검증 (end-to-end)
1. **단위 테스트** `tests/tools/test_table_extractor.py` (네트워크 無, 인메모리 fake reader 주입):
   - DBIO 단건: `<sqlString>` → 테이블 정확히 추출(`:bind`·힌트·UNION·엔티티 언이스케이프 포함). 픽스처는 `remote_ap_server/files/.../DYNAMICSQL/{PFO_STCK_MA_DS200,PFO_FUND_BS_DF037}`, `.../EXECSQL/PFO_MNCM_CLCD_HT_EI901` 활용(기대: 각각 {PFO_STCK_MA,TRU_STCK_ITMS_HT,PFO_BRWN_STCK_MA,PFO_SPA_MA,PFO_SPA_ITMS_HT} / {PFO_FUND_BS,PFO_TAMI_SM,PFO_CLFD_REVS_STPR_MA} / {PFO_MNCM_CLCD_HT}).
   - DYNAMICSQL·EXECSQL 루트 태그 **둘 다** `<sqlString>` 추출되는지.
   - Service→DBIO 1홉, Service→Biz→DBIO **재귀**, **순환 참조**(A→B→A) 무한루프 안 빠지는지.
   - `SourceNotFound` 전파, 접미/패턴 안 맞는 리터럴 무시.
   - `mapper.extract_sql`/`ids.scan_ref_ids`/`ids.classify` 순수함수 직접 테스트(기존 test 스타일과 동일한 직접 호출).
2. **수동**: `uvicorn app.main:app --reload` → Table Extractor 탭에서 타입/ID 입력 후 추출 → 좌측 테이블·우측 SQL 확인. 또는 `curl -X POST /table-extractor/extract -d '{"id_type":"dbio","id":"PFO_STCK_MA_DS200"}'`.
3. **회귀**: `pytest` 전체(기존 42 + 신규) 통과.

## 남은 확정 항목 (사용자 제공 = 설정값, 설계 아님)
- `ID_TYPES`의 실제 **접두사 / 디렉토리 / 확장자** (Service/Batch/Biz가 `.xml`인지 `.java`인지 등 — 스캔은 언어 무관 정규식이라 확장자만 경로에 영향).
- 후속 PR: `SftpSourceReader` 접속 정보(호스트/계정/기준경로)를 환경변수로 주입 + 라우터 배선.

---

## 진행 상황 (2026-08-04 기준 — 내일 이어서)

### ✅ 완료
1. **프론트 화면**: 컨트롤 행(드롭박스[DBIO/Service/Batch/Biz] + 입력 + 추출하기) + 좌우 1:1 워크스페이스(좌=테이블목록 placeholder, 우=`delete insert sql` textarea). `추출하기`는 아직 무동작.
2. **`router.py` 스켈레톤**: `ExtractRequest{id_type: Literal, id}` / `ExtractResponse{tables, sql, dbios}`, `POST /table-extractor/extract`. 빈 id→400, 잘못된 타입→422. **현재 501 반환**(서비스 미구현), 서비스 연결부는 주석으로 대기. TestClient로 상태코드 검증 완료, 앱 정상 부팅.
3. **`app/common/source.py`** (원래 tool에 뒀다가 **common으로 이동** — 도메인 지식 없는 범용 I/O 인프라, text.py와 같은 범주):
   - `SourceReader`(runtime_checkable Protocol, `read(path)->str`)
   - `SourceNotFound`(파일 부재→404) / `SourceError`(접속·인증·전송 실패→후속 502 매핑)
   - `SftpSourceReader`(paramiko 기반, host/port/user/password/base_dir 주입, `read`마다 connect→open_sftp→open/read→decode. 파일 없음→SourceNotFound, 인증/접속 실패→SourceError, 호스트키 `AutoAddPolicy`). 회사 서버 프로토콜이 SFTP라 ftplib이 아니라 paramiko.
   - **`LocalSourceReader`는 삭제함** — 개발/검증은 Docker SFTP, 단위테스트는 인메모리 fake로 대체.
   - `paramiko>=3.0` → pyproject **런타임** deps에 추가. 로거 `no_gada.source`.
4. **Docker SFTP 테스트 환경** (회사 서버 없이 127.0.0.1로 실코드 경로 검증):
   - `remote_ap_server/`(atmoz/sftp): 127.0.0.1:**2222**, 계정 **testuser/testpass**, base=`src`, 픽스처 = `remote_ap_server/files/…/publish_ecams/resource/`.
   - **실접속 검증 완료**: `docker compose up -d` 후 `SftpSourceReader("127.0.0.1", port=2222, user="testuser", password="testpass", base_dir="src")`로 3개 DBIO 픽스처 읽기 성공, 없는 파일→SourceNotFound, 읽은 `<sqlString>`→`extract_tables`→기대 테이블 일치(PFO_STCK_MA_DS200/PFO_FUND_BS_DF037/PFO_MNCM_CLCD_HT_EI901).

### ⏭️ 다음 (내일)
- [ ] **`ids.py`**: 실물 경로 규칙(`publish_ecams/resource/<PROG>/<SQLTYPE>/<ID>/<ID>.xml`) 반영. `resolve_path(id_type, id, reader)`는 DBIO를 트리 탐색으로 위치 결정 / `classify(id)`(접미·패턴) / `scan_ref_ids(text)`. ※ Service/Batch/Biz 규칙은 상위 `.c` 실물 확인 후 확정.
- [ ] **`mapper.py`**: ProFrame DBIO XML → SQL. `ElementTree`로 **`sqlString` 텍스트** 수집(루트 태그 무관), 엔티티/CDATA 해제. **바인드 치환 없음**(이미 `:name`). ※ 픽스처: `remote_ap_server/files/.../{DYNAMICSQL,EXECSQL}/...`.
- [ ] **`source.py` 나열 메서드**: 트리 탐색용 `list`/`glob`를 `SourceReader`에 추가(SFTP `listdir`+fake 구현). ← `resolve_path` DBIO 탐색이 의존.
- [ ] **`service.py`**: `extract(id_type, id, reader)` + 재귀 `_collect`(visited로 순환 차단, dbio 종료 / 그 외 scan→classify→재귀). 수집 SQL 각각 `extract_tables`→합집합. DBIO 파싱 실패는 skip+warning.
- [ ] **`router.py` 연결**: 501 제거, 주석부 활성화. `default_reader()`는 env(`NOGADA_SFTP_HOST`/`_PORT`/`_USER`/`_PASS`/`_BASE`)에서 `SftpSourceReader` 생성(기본 `remote_ap_server` Docker SFTP 127.0.0.1:2222/testuser/testpass/base=src). ※ `app/common/source.py`로 이동됨.
- [ ] **프론트 `#te-submit`** fetch 연결(좌 목록/우 SQL 채움, 에러박스/스피너 재사용).
- [ ] **테스트** `tests/tools/test_table_extractor.py`: 인메모리 fake reader로 단위(재귀/순환/부재/DYNAMICSQL·EXECSQL 루트), Docker SFTP(`remote_ap_server`)로 `SftpSourceReader` 통합.

### ⚠️ 원래 계획 대비 바뀐 점 (위 본문과 상충하는 부분은 이 진행상황이 최신)
- `source.py` 위치: `app/tools/table_extractor/` → **`app/common/source.py`**.
- 소스 reader: `LocalSourceReader` **삭제** → 개발/운영 모두 `SftpSourceReader`(개발은 Docker SFTP), 테스트는 인메모리 fake.
- 라우터 기본 reader: `LocalSourceReader(TE_SOURCE_DIR)` → **`SftpSourceReader`(env, 기본 Docker SFTP 2222)**.

### 🔴 사용자 제공 현황
- ✅ **DBIO 실물 확인 완료**(사진→`remote_ap_server` 픽스처): DYNAMICSQL/EXECSQL 포맷, `<sqlString>` 텍스트, Oracle `:name` 바인드. 경로 = `publish_ecams/resource/<PROG>/<SQLTYPE>/<ID>/<ID>.xml`.
- ⏳ **미제공**: Service/Biz(`.c`) 파일에서 하위 DBIO ID가 박힌 실제 모습 → `classify`/`scan_ref_ids`/Service·Batch 경로 규칙 확정에 필요.

### 실행 메모
```bash
source .venv/bin/activate && pip install -e ".[dev]"       # paramiko 포함
(cd remote_ap_server && docker compose up -d)                  # Docker SFTP (127.0.0.1:2222, testuser/testpass)
# 접속 확인: SftpSourceReader("127.0.0.1", port=2222, user="testuser", password="testpass", base_dir="src").read("truap01dap1/.../PFO_STCK_MA_DS200.xml")
uvicorn app.main:app --reload                               # 웹앱
pytest                                                      # 회귀(현재 72개)
```

---

## 진행 상황 (2026-08-08 기준)

### ✅ DBIO 추출 파이프라인 완료
- **REST 계약 변경**: `POST /table-extractor/extract`(바디) → **`GET /table-extractor/{id_type}/{prog}/{id}`**(경로 파라미터). 부작용 없는 멱등 조회라 GET이 자연스럽고, 세 값 다 짧은 식별자라 URL에 넣는 데 문제없음. `id_type`/`prog` 타입은 `app/common/proframe.py`(`IdType`/`Prog` `Literal`)로 공용화 — ProFrame ID 분류 체계 자체라 다른 툴에서도 재사용될 값. `prog`는 실물 7개(`PCSP PCSH NCOM NCSP PCOM PPFR RLGR`) 전부 반영(화면 콤보박스도 동기화).
- **DBIO 경로 해석 설계가 원래 계획과 달라짐**: `prog`를 사용자가 이미 명시적으로 주므로 트리 전체를 나열할 필요가 없어졌고, 남은 미지수였던 `SQLTYPE`도 **ID 끝 2글자 코드**(`DS200`의 `DS` 등)로 확정됨(`DF/DS/DI/DU/DD`→DYNAMICSQL, `EI/EU/ED`→EXECSQL, `PI/PU/PD/PS/PF`→PERSIST, `VF/VS`→VIEW). 그래서 **`SourceReader.list()/glob()` 추가 없이** `classify_sqltype(id)` 정규식 매칭 → 경로 1회 조합 → `read()` 1회로 끝남. 매칭 안 되는 접미사는 `UnknownSqlType`(→ 400)로 명확히 거부. 처음엔 `app/tools/table_extractor/ids.py`로 만들었다가, "DBIO ID → 원격 XML 읽기"는 다른 툴에서도 소비처가 늘어날 동작이라 **`app/common/dbio.py`로 이동**(모듈명도 더 직관적으로 개명).
- **`mapper.py`**: `ElementTree` + 로컬네임(`sqlString`) 매칭으로 루트 태그/네임스페이스 무관하게 SQL 추출, XML 파싱 실패 시 정규식 폴백. 실물 DYNAMICSQL(네임스페이스 없음)·EXECSQL(루트에 네임스페이스 있고 자식은 `xmlns=""`로 리셋) 둘 다 fixture로 검증.
- **`service.py`**: `extract(id_type, prog, id, reader)` — 지금은 `id_type == "dbio"`만 구현, 그 외는 라우터에서 501. reader 팩토리 `default_reader()`는 **`app/common/source.py`**에 있고 env(`NOGADA_SFTP_HOST/_PORT/_USER/_PASS/_BASE`) 기반, 기본값 Docker SFTP. FastAPI `Depends(default_reader)`로 라우터에 주입해 테스트에서 `app.dependency_overrides`로 인메모리 fake reader 교체 가능.
- **`router.py`**: 501 스텁 제거(DBIO 한정), `UnknownSqlType`→400 / `SourceNotFound`→404 / `ExtractionError`→400 매핑. `id_type != "dbio"`는 여전히 501.
- **테스트**: `tests/tools/test_table_extractor.py` 30개 — `mapper`/`dbio` 순수 함수 단위, 라우터 통합(성공/404/400/422/501/405 전부), 실 Docker SFTP로 `curl`까지 수동 검증 완료(`PFO_STCK_MA_DS200`→기대 테이블 5개 정확히 일치).

### ⏭️ 남은 것
- [ ] Service/Batch/Biz `id_type` 구현 — 상위 `.c` 파일 실물(하위 DBIO ID가 박히는 모습)을 아직 못 봐서 `classify`/`scan_ref_ids`/경로 규칙 미확정. 재귀 해석(`visited`로 순환 차단) 로직도 이때 추가.
- [ ] 프론트 `#te-submit` fetch 연결 — 지금 API가 `GET /table-extractor/{id_type}/{prog}/{id}`이므로 콤보박스/드롭박스/입력값으로 URL 조합해 fetch, 좌측 테이블 목록/우측 SQL 채우기, 에러박스·스피너 재사용.

---

## 진행 상황 (2026-08-10 기준 — DBIO 경로 평면화 + 네이밍 정리)

> **이 섹션이 Part 1의 최신**이다. 위 2026-08-04·08-08 로그의 `publish_ecams/resource/<PROG>/<SQLTYPE>/<ID>/<ID>.xml` 경로, `read_dbio_xml`에 `prog/resource_group` 인자, `IdType`/`Prog` 명칭은 **모두 아래로 대체**됨. (Part 2가 이 섹션 이후를 더 확장한다.)

### 🔀 DBIO 실물 경로 정정 — 평면 구조
- 실물 경로는 `publish_ecams/resource/<PROG>/<SQLTYPE>/<ID>/<ID>.xml`이 아니라 **`release/dbio/xml/<ID>.xml`(완전 평면 — PROG·SQLTYPE 하위 없음)**이었다. `remote_ap_server/files/…/`의 DBIO XML 5개(신규 복원 `AIS_ACCSUBJ_BS_VF001` + 기존 `PFO_CLCD_MIP_MA_VF001`·`PFO_FUND_BS_DF037`·`PFO_MNCM_CLCD_HT_EI901`·`PFO_STCK_MA_DS200`)를 이 디렉토리로 이동, 옛 `publish_ecams/` 트리는 제거.
- **`app/common/dbio.py`**:
  - `DBIO_RESOURCE_ROOT` = `/src/truap01dap1/proframe/proframe5.0/release/dbio/xml`.
  - `read_dbio_xml(file_id, reader)` — **`resource_group` 인자 제거**(평면이라 PROG 불필요). 경로 = `{ROOT}/<ID>.xml` 1회 조합.
  - `classify_sqltype(file_id)`는 이제 **경로 결정용이 아니라 접미사 검증 전용**으로 남는다: 인식 못 하는 접미사(`SQL_TYPE_BY_SUFFIX`/`ID_SUFFIX_RE` 미매칭)를 `UnknownSqlType`으로 던져 잘못된 ID를 파일없음(404)보다 명확한 **400**으로 먼저 거른다. (SQLTYPE 매핑 표·정규식은 그대로 유지 — 검증 게이트로 재사용.)
- **`service.py`**: `read_dbio_xml(file_id, reader)` 호출로 수정(`resource_group`은 로그·라우트 계약용으로만 유지).

### 🏷️ 공용 타입·파라미터 네이밍 정리
- `app/common/proframe.py`: **`IdType` → `Module_Type`**, **`Prog` → `ResourceGroup`**(값 집합은 동일: `dbio/service/batch/biz`, `PCSP PCSH NCOM NCSP PCOM PPFR RLGR`).
- `extract`/`read_dbio_xml` 파라미터: **`id_type` → `module_type`**, **`prog` → `resource_group`**, **`id` → `file_id`**.

### 🔗 URL 계약은 그대로 유지
- **`GET /table-extractor/{module_type}/{resource_group}/{file_id}`** 유지. DBIO에선 `resource_group`이 파일 위치 탐색에 쓰이지 않지만, **향후 Service/Batch/Biz 확장 시 `compile/<PROG>/src/{batch,module,serviceModule}/…` 경로 결정에 실제로 사용**할 예정이라 라우트·프론트 계약을 바꾸지 않는다. `module_type`/`resource_group`은 계속 `Literal`이라 잘못된 값은 FastAPI 422.

### ✅ 테스트
- `tests/tools/test_table_extractor.py`: `FIXTURE_ROOT`·기대 경로(`DS200_PATH`/`EI901_PATH`)를 평면으로, `read_dbio_xml` 호출에서 `resource_group` 인자 제거. `classify_sqltype`(→400)·`SourceNotFound`(→404)·`Literal`(→422) 검증은 그대로.
- **전체 103개 통과.**

---

# Part 2 — 재귀적 테이블 추출: Service / Batch / Biz 모듈 지원 (2026-08-13~08-16)

**상태: 구현 완료 + 후속 확장 반영** (2026-08-16 기준, `pytest` 154개 그린). 아래 "설계"는 실제 구현된 최종 형태를 기록한다. 남은 항목은 맨 아래 "미해결 / 후속" 참고.

**2026-08-13 이후 추가된 것**(Part 2 최초 작성 이후):
- **재귀 참조 제외 목록**(설정 파일 기반) — 섹션 8.
- **프론트엔드 batch 표시** — 섹션 9. (섹션 6 시절 "프론트엔드 미반영" 후속 항목 해소)
- **SFTP 세션 재사용(성능개선)** — 섹션 10.
- **매핑파일 기반 find 가속(성능개선, 1단계)** — 섹션 11.
- 로컬 SFTP 픽스처 디렉터리 리네임: `remote_server/` → **`remote_ap_server/`**(사용자 작업, 이 문서 전체의 경로 표기도 갱신).
- 실물 회귀 픽스처 대폭 확충: `MPCOM_GetBzopDate.c`가 참조하는 DBIO 8개(`PFO_DATE_MNGM_BS_VS004~011`) XML 전부 확보 → 섹션 검증의 "실 end-to-end 미실시" 항목 해소. `SPCSP53619C.c`(DBIO 2개 + biz 2개 `MPCOM_CalcFndRntn`/`MPCOM_CalcBmRnrt` + 그 DBIO 2개)와 `SRLGR96602A.c`(DBIO 7개 + batch 소스 `BRLGRPRP0001.c`)도 재귀 전체가 skip 없이 완주하도록 픽스처 완성.
- `SRLGR96602A.c` 실물 픽스처에서 **진짜 버그 발견·수정**: `MNT_FUND_INFR_HT_VF016`/`TRU_PBHL_BS_VF501`이 `pfmDbioCloseCursorArray(...)` 형태로만 등장하고 실제 open/select는 전무 — 다른 노드에서 복붙된 죽은 정리코드였다. 소스에서 제거(오탐 잔재 주석도 정리) → `scan_module_refs`가 더 이상 이 둘을 잡지 않음.

## Context
기존 `table_extractor`는 **DBIO 한 종류만** 처리했다: `service.extract`가 `module_type=="dbio"`가 아니면 `NotImplementedError`(라우터가 501)로 막고, `read_dbio_xml`로 XML 1개를 읽어 `<sqlString>`→테이블을 뽑는 단일 단계였다. Service/Batch/Biz는 **C 소스 파일**이며, 그 안에서 DBIO(및 다른 모듈)를 참조한다. 목표는 이 세 타입의 진입 모듈에서 시작해 **참조를 재귀적으로 따라가** 도달한 모든 DBIO의 SQL에서 테이블을 합산하는 것 — 이제 구현됨.

세 타입은 "파일을 읽고 → 내부 참조를 스캔 → DBIO는 XML에서 SQL 추출, 모듈이면 더 파고듦"이라는 점에서 동일하고, **파일 위치 규칙만** 다르다.

## Confirmed (사용자 제공)
- **참조 문법 = 대상 타입을 그대로 알려줌** (ID 접두 추정 불필요 — `MZCOM_...`처럼 업무그룹이 7종 밖인 경우도 있어 접두 분류는 신뢰 불가):
  - DBIO(리프): `PFM_TRYNJ(pfmDbioSelect("PFO_..._DS101", ...))`, `pfmDbioOpenCursorArray("..._DF100"/"..._VF314"/"..._PF001", ...)`, `pfmDbioDml("..._PI001", ...)` — 즉 `pfmDbio*("<ID>"`.
  - Biz: `PFM_TRYNJ(pfmDlCall("MZCOM_ChkDynSql", "MZCOM_ChkDynSql", ...))` — 첫 문자열 인자가 biz ID.
  - Service: `PFM_TRYNJ(pfmServiceModuleCall(&in, &out, &linkHeader, sizeof(SPCOM48990B_IN), ...))` — service ID는 `sizeof(<ID>_IN)`의 구조체명에서 뽑음. **주의**: 보유 픽스처에는 `pfmServiceModuleCall` 실례가 없다(전부 `pfmDlCall`만 사용) — 이 규칙은 아직 합성 텍스트로만 회귀 고정돼 있다(`tests/tools/test_refs.py::test_service_call_sizeof_in_struct_name`).
  - Batch: **전용 호출 매크로가 없다.** 배치는 항상 고정된 biz 모듈 `MZPFM_BatchLinkCall`(`pfmDlCall("MZPFM_BatchLinkCall", "MZPFM_BatchLinkCall", &in, &out)`)을 통해서만 간접 호출된다. 실제 대상 배치 ID는 호출 인자 안이 아니라 그 직전 `STRCPY(temporaryInput.bat_code, "B<리소스그룹4자리><suffix>")`처럼 **별도 대입문의 문자열 리터럴**로 존재하며(예: `"BRLGRPRP0001"`), 런타임 동적 조립 없이 항상 하드코딩된다. 즉 피호출 배치는 `"B(PCSP|PCSH|NCOM|NCSP|PCOM|PPFR|RLGR)[A-Z0-9]+"` 정규식으로 **파일 전체를 리터럴 스캔**하면 잡힌다(콜 매크로 인자 위치가 아니라는 점이 dbio/biz/service와 다름). 실물 배치서비스 `RLGR/src/serviceModule/SRLGR96602A/SRLGR96602A.c`에서 이 정규식으로 오탐 없이 `"BRLGRPRP0001"` 1건만 정확히 검출해 확인함.
  - **batch는 재귀하지 않기로 결정**(구현 중 확정): 배치는 독립적으로 기동되는 별도 잡이라 현재 진입 모듈의 테이블 추출 범위로 보기 어렵다. 그래서 `extract_from_module`은 `ref_type=="batch"`를 만나면 소스를 조회·재귀하지 않고 **참조된 배치 ID만 기록**해 화면에 보여준다(`ExtractResult.batches`, 아래 섹션 4·5 참고).
- **위치**: `compile/<PROG>/src/{serviceModule/<ID>/<ID>.c | batch/<ID>.c | module/<ID>.c}`. `COMPILE_ROOT = f"{PROFRAME_ROOT}/compile"`.
- **discovered 모듈의 resource_group** = `compile`에서 **find**(디렉토리 나열 후 후보 read). 최상위 모듈은 프론트가 준 `resource_group`을 직접 사용. (추후 "매핑파일 우선 → 없으면 find" 확장.)
- 1차 구현 범위 = **재귀 프레임워크 전체**. → 완료.

## 재사용 자산 (그대로 활용)
- `app/common/sql.py::extract_tables` / `ExtractionError` — SQL→테이블 (변경 없음).
- `app/common/dbio.py::read_dbio_xml(file_id, reader)` / `classify_sqltype` / `UnknownSqlType` — DBIO 리프 (변경 없음, `DBIO_RESOURCE_ROOT`만 `PROFRAME_ROOT` 조합으로 변경).
- `app/tools/table_extractor/mapper.py::extract_sql(xml)` — DBIO XML→SQL (변경 없음).
- `app/common/source.py::SourceReader/SftpSourceReader/SourceNotFound/SourceError` — I/O 경계(`listdir` 추가됨).
- `app/common/proframe.py::Module_Type/ResourceGroup` (그대로) + **`PROFRAME_ROOT`(신규)**.
- `app/common/csource.py::strip_comments` — C 소스 주석(`//`, `/* */`) 제거, 문자열/문자 리터럴 보존(신규, 툴 무관 공용).

## 설계 (구현된 형태)

### 1. `SourceReader`에 `listdir` 추가 — `app/common/source.py`
```python
def listdir(self, path: str) -> list[str]: ...   # 해당 디렉토리의 항목명. 없으면 SourceNotFound.
```
- `SftpSourceReader`: `read`/`listdir`가 접속 로직(`_connect`)을 공유하도록 리팩터링, 호출당 open/close는 그대로. 오류 매핑은 `read`와 동일(`SourceNotFound`/`SourceError`).
- 1레벨 나열만 필요(타입→하위디렉토리가 구조적으로 정해져 있어 후보 경로를 조립할 수 있음).

### 2. `app/common/proframe.py`에 `PROFRAME_ROOT` 추가
`dbio.py`의 `DBIO_RESOURCE_ROOT`와 `module_src.py`의 `COMPILE_ROOT`가 서버/버전 고정 접두(`/src/truap01dap1/proframe/proframe5.0`)를 중복 리터럴로 갖고 있던 걸 한 곳으로 모았다:
```python
PROFRAME_ROOT = "/src/truap01dap1/proframe/proframe5.0"
```
두 파일은 각자 하위 루트만 조합: `DBIO_RESOURCE_ROOT = f"{PROFRAME_ROOT}/release/dbio/xml"`, `COMPILE_ROOT = f"{PROFRAME_ROOT}/compile"`.

### 3. `app/common/module_src.py` (신규) — 모듈 C 소스 위치·조회 (dbio.py의 자매)
계획 당시 이름은 `compile_src.py`였으나 **`module_src.py`로 확정**(dbio.py와의 대칭성 — "모듈(service/batch/biz) 소스 조회"라는 역할이 이름에 드러남, `dbio.py`가 이미 DBIO 리프를 전담하므로 겹치지 않음).
```python
COMPILE_ROOT = f"{PROFRAME_ROOT}/compile"
MODULE_SUBDIR = {"service": "serviceModule", "batch": "batch", "biz": "module"}

def _relpath(module_type: Module_Type, file_id: str) -> str: ...          # service: serviceModule/<ID>/<ID>.c, batch/biz: <sub>/<ID>.c
def module_path(module_type: Module_Type, resource_group: str, file_id: str) -> str: ...   # 최상위(그룹 알 때) 직접 경로
def read_module_source(module_type, file_id, reader, resource_group: str | None = None) -> str:
    # resource_group 있으면 module_path로 직접 read (최상위).
    # 없으면(=재귀 중 발견된 참조) COMPILE_ROOT를 listdir해 각 업무그룹 후보 경로를 read 시도 → 첫 성공 반환. (find)
    # 못 찾으면 SourceNotFound.
```
- `resource_group`은 `ResourceGroup`(7종 Literal)이 아니라 `str`로 넓게 받는다 — find로 발견되는 그룹은 7종 밖(`ZCOM` 등)일 수 있어 `module_path`/`read_module_source` 자체는 값을 검증하지 않는다(검증은 라우터의 최상위 요청 파라미터에서만).
- 순수 I/O 위치 해석만 담당 — dbio.py와 마찬가지로 `refs.py`/`mapper.py`(툴 전용) 의존 없음. 재귀·타입 판별·SQL 추출 조합은 전부 `service.py`(오케스트레이션)에 있다 — common→tool 역방향 의존을 만들지 않기 위한 의도적 경계.
- 테스트: `tests/common/test_module_src.py`.

### 4. `app/tools/table_extractor/refs.py` (신규) — 타입 포함 참조 스캔 (mapper.py의 자매, 툴 전용)
```python
def scan_module_refs(text: str) -> list[tuple[Module_Type, str]]:
    # 내부에서 csource.strip_comments로 먼저 주석 제거(extract_tables가 sanitize_text/strip_db_links를
    # 내부에서 호출하는 것과 동일 패턴 — 호출부가 별도로 전처리할 필요 없음).
    # 이후 정규식 4종으로 매칭 → 등장 위치순 정렬 → (type, id) 튜플로 중복 제거.
    #   pfmDbio\w*\(\s*"([A-Z0-9_]+)"                                    -> ("dbio", id)
    #   pfmDlCall\(\s*"([A-Za-z0-9_]+)"                                   -> ("biz", id)
    #   pfmServiceModuleCall\([\s\S]{0,300}?sizeof\(\s*([A-Za-z]\w*)_IN\b -> ("service", id)
    #   "B(PCSP|PCSH|NCOM|NCSP|PCOM|PPFR|RLGR)[A-Z0-9]+"                  -> ("batch", id)
    #     ↑ 다른 규칙과 달리 콜 매크로 인자가 아니라 파일 전체 리터럴 스캔으로 잡는다.
    #     pfmDlCall("MZPFM_BatchLinkCall", ...) 자체는 biz 규칙에도 걸려 ("biz","MZPFM_BatchLinkCall")로도
    #     같이 나온다 — 의도된 동작(그 이름의 소스 파일은 없어 재귀 중 SourceNotFound skip이 정상 부분성공).
```
- 콜 매크로로 타입을 얻으므로 ID-접두 분류기는 불필요.
- **주석 처리 필수 — 실증됨**: ProFrame 코드젠이 실행되지 않는 예시 코드를 `//`/`/* */`로 통째로 주석 처리해 남겨두는데, 그 안에도 `pfmDbioCloseCursorArray("OK_IMSI_META_VF001")`처럼 콜 매크로 형태 그대로인 죽은 코드가 있다(`SPCSP53619C.c` 450번 줄 실증). `csource.strip_comments`가 문자열/문자 리터럴은 보존하면서 이걸 제거한다(`tests/common/test_csource.py`, `tests/tools/test_refs.py::test_dead_code_in_comment_not_captured`).
- `service` 정규식은 `pfmServiceModuleCall\(` 자체를 앵커로 요구해, 실물에 흔한 `bzero(&in, sizeof(X_IN))`(입력구조체 초기화, `pfmDlCall`용) 같은 무관한 `sizeof(_IN)`을 service로 오탐하지 않는다(`test_bzero_sizeof_in_without_service_call_not_captured`로 회귀 고정).
- 테스트: `tests/tools/test_refs.py` (실물 픽스처 3개 + 합성 케이스 10건).

### 5. `service.py` 재귀 — `app/tools/table_extractor/service.py`
계획 당시엔 클로저 기반 `collect()` 하나를 구상했으나, 실제로는 **`extract_from_dbio`(리프)와 `extract_from_module`(재귀)로 분리**해 각각 단위 테스트하기 쉽게 했다(사용자 제안).
```python
def extract(module_type, resource_group, file_id, reader) -> ExtractResult:
    if module_type == "dbio":
        return extract_from_dbio(file_id, reader)
    return extract_from_module(module_type, resource_group, file_id, reader)

def extract_from_dbio(file_id, reader) -> ExtractResult:
    ...  # XML 조회 → mapper.extract_sql → extract_tables (기존 단일-DBIO 로직 그대로)

def extract_from_module(module_type, resource_group, file_id, reader, visited=None) -> ExtractResult:
    top_level = visited is None
    if visited is None:
        visited = set()
    visited.add(file_id)

    try:
        text = read_module_source(module_type, file_id, reader, resource_group=resource_group)
    except (SourceNotFound, SourceError):
        if top_level:
            raise                      # 최상위 실패 → 라우터가 404/503
        logger.warning(...); return ExtractResult(tables=[], sql="", dbios=[])   # 재귀 중 실패 → skip

    for ref_type, ref_id in scan_module_refs(text):
        if ref_id in visited:
            continue
        if ref_type == "batch":
            visited.add(ref_id); batches.add(ref_id); continue     # 소스 조회/재귀 안 함(정책)
        if ref_type == "dbio":
            visited.add(ref_id)
            try: result = extract_from_dbio(ref_id, reader)
            except (SourceNotFound, SourceError, UnknownSqlType, ExtractionError): logger.warning(...); continue
        else:
            result = extract_from_module(ref_type, None, ref_id, reader, visited=visited)   # discovered → find
        tables.update(result.tables); ...; batches.update(result.batches)

    return ExtractResult(tables=sorted(tables), sql=";\n".join(sqls), dbios=dbios, batches=sorted(batches))
```
- **순환 차단**: `visited`(file_id 집합, 재귀 전체가 공유) — 타입이 달라도 같은 ID는 한 번만 처리.
- **최상위 vs 재귀 구분**: `visited` 인자가 `None`인 최초 호출만 소스 조회 실패를 그대로 전파(라우터 4xx/5xx). 재귀 호출(`visited` 전달됨)은 실패를 skip+warn(부분성공).
- **batch는 재귀하지 않음**(위 Confirmed 참고): `ExtractResult`에 `batches: list[str]` 필드를 추가해 참조된 배치 ID만 집계·노출한다.
- `dbios`는 도달한 DBIO ID 순서 목록(기존 `[file_id]` 단일에서 자연 확장).
- 테스트: `tests/tools/test_table_extractor.py`의 "service.extract_from_module (재귀)" 섹션.

### 6. 라우터 — `app/tools/table_extractor/router.py`
- `module_type != "dbio"` → **501 블록 제거**.
- 비-DBIO인데 `resource_group`이 없으면(2세그먼트) → **400**("resource_group required for {module_type}").
- 에러 매핑: `SourceError`→**503**(신규) 추가. `SourceNotFound`(최상위)→404, `UnknownSqlType`/`ExtractionError`→400 유지.
- `ExtractResponse`에 `batches: list[str]` 필드 추가(참조만 되고 소스는 안 본 배치 ID, 화면 표시용) — 계획에는 없던 항목, 구현 중 추가.

### 7. 테스트
- `tests/common/test_csource.py`(신규): `strip_comments` 단위 8케이스.
- `tests/common/test_module_src.py`(신규): `module_path`/`read_module_source`(직접 read·find·find 실패) 7케이스.
- `tests/tools/test_refs.py`(신규): `scan_module_refs` 10케이스(dbio/biz/batch는 실물 픽스처, service는 합성, 주석 오탐 방지 포함).
- `tests/tools/test_table_extractor.py`(확장): `FakeReader`에 `listdir` + 호출 기록(`read_calls`/`listdir_calls`) 추가.
  - biz→DBIO 재귀: 실물 `MPCOM_GetBzopDate.c`(8개 DBIO 전부 도달, XML은 합성 주입).
  - service→biz→dbio 재귀 + find(discovered biz 그룹 발견) + 순환 참조(A↔B, 깨지면 RecursionError로 즉시 드러남) + nested 실패 skip(부분성공).
  - batch 참조: 실물 `SRLGR96602A.c` — `batches == ["BRLGRPRP0001"]`이면서 그 ID로 `read`/`listdir` 호출이 전혀 없었음을 직접 검증(소스를 안 본다는 걸 스파이로 증명).
  - 최상위 실패 전파, `extract()` 디스패치.
  - 라우터: `GET /table-extractor/biz/PCOM/MPCOM_GetBzopDate`(3세그) 200, 2세그 400, 최상위 파일없음 404. 옛 `test_non_dbio_id_type_still_not_implemented`(501 기대)는 성공/400/404 케이스로 교체.

### 8. 재귀 참조 제외 목록 (신규, 2026-08-15 추가) — `app/tools/table_extractor/excludes.py`
특정 DBIO/모듈 ID를 재귀 집계에서 항상 빼고 싶다는 요구로 추가. 설계 결정: **고정 목록**(코드/설정 파일 기반, 요청마다 바뀌는 게 아님) + **재귀 참조에만 적용**(최상위로 직접 요청한 ID는 무관하게 처리) + **설정 파일로 관리**(코드 상수가 아니라 사람이 편집).
```python
DEFAULT_EXCLUDED_REFS_PATH = "config/excluded_refs.txt"

def load_excluded_refs(path: str | None = None) -> set[str]:
    # path 없으면 NOGADA_EXCLUDED_REFS_PATH 환경변수 → 기본값 순.
    # 파일 없으면 빈 set(선택적 기능, 미설정 시 아무것도 제외 안 함).
    # 포맷: 한 줄에 ID 하나, `#` 뒤는 주석, 빈 줄 무시.
```
- `config/excluded_refs.txt`(저장소 루트, `app/` 밖) — `pyproject.toml`의 `packages.find`가 `app*`만 패키징하므로 코드가 아닌 런타임 설정 데이터는 원래도 `app/` 밖(`remote_ap_server/`, `remote_db_server/`, `logs/`와 동일 위치 규칙)에 두는 게 이 저장소 컨벤션과 맞다.
- 적용 지점은 `service.py::extract_from_module`의 참조 루프, **`visited` 체크 바로 옆**: `if ref_id in excluded: continue`(타입 무관, ID 문자열 하나로 통일 체크 — dbio/biz/service/batch 구분 없음). `excluded`는 `visited`처럼 재귀 전체에 파라미터로 스레딩되고, 최초 호출(`visited is None`)일 때만 `load_excluded_refs()`로 1회 로드.
- **주의(실사용 중 발견)**: 매칭 대상은 **참조 ID 그 자체**지 테이블명이 아니다. 예컨대 DBIO `TRU_CMN_SRCH_SLCT_TM_EI001`을 빼고 싶다면 그 ID를 그대로 넣어야 하고, 테이블명 `TRU_CMN_SRCH_SLCT_TM`을 넣으면 매칭이 안 돼 그대로 추출된다(둘은 별개 문자열).
- 실사용 예: `MZPFM_BatchLinkCall`(batch 간접호출용 고정 biz 모듈 — 소스가 없어 항상 `SourceNotFound`로 skip되던 걸 아예 조회 시도조차 안 하게), `MZCOM_GetSeqNo`/`MMCMP_ProcJobFundCrtn`(소스 없는 biz 참조).
- 테스트: `tests/tools/test_excludes.py`(로더 파싱 4케이스), `tests/tools/test_table_extractor.py`의 관련 케이스(재귀 중 스킵 시 `read` 호출 자체가 없음을 스파이로 검증 + 같은 ID를 최상위로 직접 요청하면 정상 처리되는지).

### 9. 프론트엔드 batch 표시 (신규) — `table_extractor.js`/`table_extractor.css`
`ExtractResponse.batches`는 라우터 도입 때부터 있었지만 화면에 아무것도 안 그리고 있었다. "발견된 batch" 섹션을 **테이블 목록 밑에, batch가 있을 때만** 추가:
- `renderTables(tables, batches)`로 시그니처 확장 — `batches`가 비어있지 않을 때만 `.te-fep-section`과 같은 시각 패턴(구분선 + 개수 배지 + 목록)의 `.te-batch-section`을 렌더.
- **버그 발견·수정**: 기존 코드가 `data.tables.length === 0`이면 `batches`를 볼 것도 없이 무조건 "추출된 테이블이 없습니다"로 조기 종료했다. 그런데 `SRLGR96602A`처럼 참조 DBIO들이 아직 없어 `tables: []`인데 `batches: ["BRLGRPRP0001"]`인 실제 응답이 있어서(당시 SFTP로 직접 재현) batch 목록이 영영 안 보이는 상태였다. `tables`·`batches` **둘 다** 비었을 때만 empty 처리하도록 고침.
- batch 항목 옆 안내문구는 "참조된 배치는 직접 조회 요청. 자동 참조 기능 지원안함"(사용자 확정 문구) — batch는 재귀 안 한다는 정책(섹션 5·6 참고)을 화면에서도 알려주는 용도.

### 10. SFTP 세션 재사용 (성능개선, 신규, 2026-08-16 추가) — `app/common/source.py`

**문제**: 재귀 추출은 참조 하나당 최소 1번(`extract_from_dbio`의 DBIO XML 조회, `extract_from_module`의 모듈 소스 조회)씩 `reader.read()`/`listdir()`를 호출하는데, 기존 `SftpSourceReader.read`/`listdir`는 **호출마다** `_connect()`로 새 `paramiko.SSHClient`를 만들어 TCP+SSH 키교환+인증을 전부 새로 하고 끝나면 바로 닫았다(재사용 없음). 여기에 `module_src.read_module_source`의 **find 폴백**(재귀 중 발견된 `service`/`biz` 참조는 소속 업무그룹을 몰라 `COMPILE_ROOT`를 `listdir` 후 `ResourceGroup` 7종을 후보로 순서대로 `read` 시도)이 겹치면, 참조 1개를 찾는 데만 최악의 경우 SSH 핸드셰이크가 최대 8번(`listdir` 1 + `read` 최대 7) 들 수 있다. 즉 총 연결 횟수가 참조 개수에 비례해 선형 증가 — 실측 전이지만 코드 검토 기준 재귀 추출의 지배적 비용 지점으로 지목됨(계산량이 아니라 I/O 왕복 횟수 문제).

**원인(기존 코드 근거)**: 원래 `read`/`listdir`는 아래처럼 짜여 있었다(git 커밋된 버전, 수정 전).
```python
def read(self, path: str) -> str:
    client = self._connect()          # 매 호출마다 지역변수로 새로 생성
    try:
        sftp = client.open_sftp()     # 이것도 지역변수
        try:
            with sftp.open(path, "r") as f:
                data: bytes = f.read()
        except FileNotFoundError as e:
            raise SourceNotFound(...) from e
        except OSError as e:
            raise SourceError(...) from e
        finally:
            sftp.close()               # 함수 끝나기 전 무조건 닫음
    finally:
        client.close()                 # 함수 끝나기 전 무조건 닫음
```
`listdir()`도 동일 구조. 두 가지가 겹쳐서 매 호출마다 세션이 끊겼다:
1. **연결이 인스턴스 상태가 아니라 함수 지역변수였다.** `client`/`sftp`가 `self._client`/`self._sftp` 같은 필드가 아니라 매 호출 안에서만 사는 지역변수라, 이전 호출의 연결을 다음 호출이 알 방법 자체가 없었다(`__init__`에도 접속 정보만 있었고 연결 객체를 담을 필드가 없었음).
2. **`finally: client.close()`가 함수 리턴 직전 무조건 실행됐다.** try/finally 구조상 정상 리턴이든 예외든 함수를 빠져나가기 전에 `sftp.close()` → `client.close()`가 실행되도록 명시적으로 짜여 있었다 — "이 함수 호출 안에서만 살아있는 연결"이 의도된 설계였다(클래스 docstring에도 원래 `` `read`마다 접속/해제하는 단순 모델(상태 없는 세션) ``이라고 적혀 있었음).

즉 재사용이 빠진 버그가 아니라, 애초에 "매번 새로 접속하고 확실히 끊는다"가 설계였던 것 — 섹션 10의 조치가 이 지역변수를 인스턴스 필드로 올리고 `finally` 강제 종료를 제거해 재사용 가능하게 바꾼 것.

**조치**: `SftpSourceReader`가 세션(`SSHClient`+`SFTPClient`)을 인스턴스에 보관하고 첫 호출에만 연결, 이후 `read`/`listdir` 호출은 재사용하도록 변경.
```python
def _ensure_sftp(self) -> paramiko.SFTPClient:
    if self._sftp is None:
        self._client = self._connect()
        self._sftp = self._client.open_sftp()
    return self._sftp
```
- 세션이 끊겨 있으면(`paramiko.SSHException`/`EOFError`/`OSError`) `_reset()`으로 정리 후 **1회 재연결해 재시도**(`FileNotFoundError`는 재시도 대상이 아니라 즉시 `SourceNotFound`).
- `close()`(반복 호출 안전) + `__enter__`/`__exit__` 컨텍스트 매니저 지원 추가.
- `default_reader()`를 일반 함수 → **`yield` 의존성**(generator)으로 전환: FastAPI가 응답 완료 후 자동으로 `reader.close()`를 호출해 세션을 정리. `Depends(default_reader)`를 쓰는 `router.py`는 코드 변경 없이 그대로 동작(FastAPI가 generator 의존성을 투명하게 처리).
- **효과**: 재귀 추출 요청 하나가 SSH 핸드셰이크 1회(+세션 끊김 시 재연결)로 끝남 — 참조 개수·find 폴백 후보 수에 비례해 늘던 연결 비용이 사실상 제거됨.
- **검증**: `pytest` 143개 전부 그린(인터페이스 변경 없음 — `tests/tools/test_table_extractor.py`는 `app.dependency_overrides[default_reader] = lambda: FakeReader(...)`로 완전히 다른 콜러블로 교체하는 방식이라 `default_reader`가 generator로 바뀌어도 무관). **로컬 Docker SFTP(`remote_ap_server/`)로 실제 세션 재사용(연결 1회 + read 다회) 확인은 미실시**(작업 시점에 Docker 데몬 미기동) — 후속 과제로 남김.
- 참고: `default_reader()`가 이제 제너레이터라 직접 호출(`default_reader()`)하면 값이 아니라 제너레이터 객체가 반환된다 — 현재 유일한 소비처가 FastAPI `Depends`뿐이라 문제없지만, 향후 다른 곳에서 직접 호출할 일이 생기면 이 점을 인지해야 함.

### 11. 매핑파일 기반 find 가속 (성능개선 1단계, 신규, 2026-08-16 추가) — `app/common/module_src.py`

**문제**: 섹션 10(SSH 세션 재사용)으로 접속 핸드셰이크 비용은 없앴지만, `read_module_source`의 find 폴백(재귀 중 발견된 `service`/`biz` 참조가 소속 업무그룹을 몰라 `COMPILE_ROOT`를 `listdir`한 뒤 후보를 하나씩 순서대로 `read` 시도)의 **왕복 횟수 자체**는 그대로다. 사내 환경은 업무그룹이 최대 30개까지 있어, 참조 1개당 최대 30회의 순차 왕복이 걸린다 — 특히 소스가 아예 없는 참조(`config/excluded_refs.txt`에 이미 등록된 사례들)는 매번 30개 전부를 실패해야 `SourceNotFound`가 나므로 항상 최악의 경우를 전액 지불한다.

**기각한 대안**: 업무그룹마다 `service`/`biz` 디렉터리 전체를 `listdir`해 `{ID: 그룹}` 인덱스를 한 번에 만드는 방식은, 각 업무그룹 디렉터리에 파일이 매우 많은 이 환경에서 그 `listdir` 자체가(파일 개수에 비례해 응답이 커짐) 오히려 참조 하나짜리 `read`(파일 개수 무관, 고정 비용)보다 무거울 수 있어 요청 경로에 넣기엔 위험하다고 판단해 기각.

**조치**: "ID→업무그룹" 매핑을 요청 경로 밖(오프라인 배치)에서 미리 만들어두고, find 폴백이 이 매핑을 먼저 참고하게 했다. 매핑에 없거나 매핑이 가리키는 그룹에서 실제로 못 찾으면(`SourceNotFound`) 기존 순차 탐색으로 자동 폴백 — 매핑이 비어있거나 오래돼도 정답이 틀리는 일은 없고, 있으면 빨라지기만 한다.

```python
# app/common/module_src.py
def read_module_source(module_type, file_id, reader, resource_group=None, group_map=None):
    if resource_group is not None:
        return reader.read(module_path(module_type, resource_group, file_id))
    if group_map:
        cached_group = group_map.get((module_type, file_id))
        if cached_group is not None:
            try:
                return reader.read(module_path(module_type, cached_group, file_id))
            except SourceNotFound:
                pass  # 매핑 stale → 아래 순차 탐색으로 폴백
    # --- 기존 순차 탐색(변경 없음) ---
    ...
```

- `build_group_map(reader)`: `COMPILE_ROOT`를 나열해 업무그룹마다 `service`/`biz` 서브디렉터리를 통째로 `listdir`, `{(module_type, file_id): group}` 매핑을 만든다. **요청 경로에서 호출 금지** — `scripts/build_module_group_map.py`(신규, 저장소 루트)에서만 호출하는 무거운 오프라인 작업.
- `load_group_map(path=None)` / `write_group_map(group_map, path)`: `excludes.py::load_excluded_refs`와 동일한 관용구(env `NOGADA_MODULE_GROUP_MAP_PATH` override → 기본 `config/module_group_map.txt` → 파일 없으면 빈 dict). 포맷은 `ID\tGROUP\tMODULE_TYPE`(3컬럼, `#` 주석 — 가독성 위해 ID를 맨 앞에 두도록 초기 설계에서 조정됨, 내부 dict 키는 여전히 `(module_type, file_id)`) — `dbio`는 평면 경로라 매핑 불필요, `batch`는 애초에 재귀·find를 안 하므로 매핑 대상은 `service`/`biz`뿐.
- `service.py::extract_from_module`에 `group_map` 파라미터 추가 — `visited`/`excluded`와 동일 패턴으로 재귀 전체에 스레딩, 최초 호출(top-level)에서 `None`이면 `load_group_map()`으로 1회 로드.
- **배치 실행 vs 소비 분리 이유**: 매핑을 만드는 `build_group_map`은 디렉터리 전체 나열(무거움)이라 오프라인에서, 매핑을 쓰는 `read_module_source`는 알고 있는 경로 하나만 여는(가벼움) 요청 경로에서 — 이 둘을 같은 함수에 두면 "가벼워야 할 요청 경로가 무거운 나열을 떠안는" 실수를 하기 쉬워 파일/함수 단위로 분리했다.
- **`config/module_group_map.txt` 위치**: `config/excluded_refs.txt`와 동일 자리(저장소 루트, `app/` 밖). 기술적 강제는 아니고(런타임은 상대경로 `open()`이라 `app/` 안에 둬도 동작함) 관례: (1) 코드 vs 운영자가 갱신하는 데이터를 저장소 최상위에서 구분, (2) 나중에 `pyproject.toml`의 `packages.find(include=["app*"])`로 wheel/이미지 패키징 시 코드 재배포 없이 데이터만 갱신 가능하게. 반면 `load_group_map`/`build_group_map` **코드**는 `app/common/module_src.py`에 둔다 — 소비처(`read_module_source`)가 common이라(다른 툴도 재사용 가능하도록 설계된 함수), common→tool 역방향 의존을 피하려면 로더도 common에 있어야 하기 때문(`excludes.py`가 tool 쪽에 있는 이유와 반대 논리 — 그쪽 소비처는 table_extractor 전용 `service.py`).
- **범위**: 이번엔 매핑을 만들고 소비하는 부분까지만 구현. **주기적 자동 갱신(cron 연동)은 범위 밖**(후속 과제) — `config/module_group_map.txt`는 헤더 주석만 있는 상태로 커밋, 실제 데이터는 사용자가 SFTP 접속 가능한 환경에서 `python scripts/build_module_group_map.py`를 수동 실행해 채운다.
- 테스트: `tests/common/test_module_src.py`(`build_group_map`/`load_group_map`/`write_group_map`/`read_module_source`의 매핑 적중·stale 폴백·매핑 없음 케이스, `listdir_calls` 스파이로 "매핑 적중 시 순차 탐색이 아예 안 일어남"을 직접 증명), `tests/tools/test_table_extractor.py`(`group_map`이 재귀 전체에 스레딩되는지, 최상위 호출이 env로 지정된 매핑 파일을 자동 로드하는지).

## 파일
- 수정: `app/common/source.py`(+`listdir`, `_connect` 리팩터), `app/common/proframe.py`(+`PROFRAME_ROOT`), `app/common/dbio.py`(`DBIO_RESOURCE_ROOT`를 `PROFRAME_ROOT` 조합으로), `app/tools/table_extractor/service.py`(재귀 분리 + `excluded` 파라미터), `app/tools/table_extractor/router.py`(501 제거·400·503·`batches`), `tests/tools/test_table_extractor.py`.
- 수정(섹션 10, 2026-08-16): `app/common/source.py`(`SftpSourceReader` 세션 재사용/재연결/`close`, `default_reader`를 `yield` 의존성으로 전환) — 테스트 변경 없음.
- 수정(섹션 11, 2026-08-16): `app/common/module_src.py`(+`build_group_map`/`load_group_map`/`write_group_map`/`DEFAULT_GROUP_MAP_PATH`, `read_module_source`에 `group_map` 옵션), `app/tools/table_extractor/service.py`(`group_map` 스레딩), `tests/common/test_module_src.py`, `tests/tools/test_table_extractor.py`.
- 신규(섹션 11): `scripts/build_module_group_map.py`(빌드 CLI), `config/module_group_map.txt`(헤더만 있는 상태로 커밋, 데이터는 수동 실행으로 채움).
- 신규: `app/common/csource.py`(C 주석 제거), `app/common/module_src.py`(모듈 위치·조회), `app/tools/table_extractor/refs.py`(참조 스캔), `app/tools/table_extractor/excludes.py`(제외 목록 로더, 섹션 8), `config/excluded_refs.txt`(제외 목록 데이터), `tests/common/test_csource.py`, `tests/common/test_module_src.py`, `tests/tools/test_refs.py`, `tests/tools/test_excludes.py`.
- 프론트엔드(섹션 9): `app/static/tools/table_extractor/table_extractor.js`(`renderTables`에 `batches` 인자 추가 + empty-처리 조건 수정), `app/static/tools/table_extractor/table_extractor.css`(`.te-batch-*`).
- 문서: 이 파일(당시 `extract_plan.md`, 이후 `plan.md`로 병합). `CLAUDE.md`는 "재귀 참조 제외 목록" 절만 반영됐고, 재귀 파이프라인 자체(라우터 흐름 서술)는 아직 미반영(아래 후속 참고).

## 검증
1. **단위/통합**: `pytest tests/tools/test_table_extractor.py tests/tools/test_refs.py tests/common/test_csource.py tests/common/test_module_src.py tests/tools/test_excludes.py` — 전부 그린.
2. **전체 회귀**: `pytest` — 143개 그린(2026-08-15 기준).
3. **수동 end-to-end(완료)**: `MPCOM_GetBzopDate.c`(biz) + 참조 DBIO 8개(`PFO_DATE_MNGM_BS_VS004~011`) 전부 실물 XML로 확보 → `service.extract_from_module`이 skip 없이 완주(테이블 `PFO_DATE_MNGM_BS` 1개로 수렴). `SPCSP53619C.c`(service)·`SRLGR96602A.c`(service) 둘 다 재귀 전체가 실물 픽스처만으로 완주하는 것까지 확인함(FakeReader에 실제 파일 내용을 그대로 주입해 검증, 합성 데이터 아님).

## 미해결 / 후속
- **SFTP 세션 재사용 실측 미실시**(섹션 10): 로컬 Docker SFTP(`remote_ap_server/`)로 "연결 1회 + read/listdir 다회" 실제 동작과, 재귀 추출 전체 소요시간 개선폭(Before/After)을 아직 측정하지 않음 — Docker 기동 후 검증 필요.
- **`CLAUDE.md` "Table Extractor 파이프라인" 절 미반영**: 아직 "지금은 `module_type == "dbio"`만 처리(그 외는 라우터가 501)"라는 구식 서술이 남아 있음 — 이번 재귀 파이프라인(`module_src.py`/`refs.py`/`csource.py`/`service.py` 재귀/`PROFRAME_ROOT`/`batches` 필드/제외 목록) 전체를 반영한 재작성 필요. (제외 목록 자체는 별도 절로 이미 추가됨.)
- **매핑파일 우선탐색 — 1단계(수동 빌드+소비) 완료, 주기 자동화 남음**(섹션 11): `read_module_source`의 find 앞단에 매핑 조회를 삽입하고 `scripts/build_module_group_map.py`로 수동 생성하는 부분까지는 구현됨. `config/module_group_map.txt`는 헤더만 있는 상태로 커밋돼 있어, 실제 가속 효과를 보려면 SFTP 접속 가능한 환경에서 이 스크립트를 한 번 실행해 데이터를 채워야 함. cron 등 주기 자동 갱신 연동은 아직 없음(사용자 요청 시 진행).
- **service `sizeof(_IN)` 정규식**: 실물 샘플이 아직 하나도 없음(보유 픽스처는 전부 `pfmDlCall`만 사용) — `pfmServiceModuleCall` 실물 확보 시 회귀로 검증 필요.
- **회귀 테스트 미보강**: 새로 확보된 실물 픽스처(`SPCSP53619C.c`의 `MPCOM_CalcFndRntn`/`MPCOM_CalcBmRnrt` 경유 재귀, `SRLGR96602A.c`의 DBIO 7종 + batch)가 아직 `tests/tools/test_table_extractor.py`의 정식 회귀 케이스로는 안 들어가 있음(수동 스크립트로만 검증) — 다음 손댈 때 정식 테스트로 승격 권장.
- **제외 목록 프론트 노출 없음**: `excluded_refs.txt`에만 있고 화면에는 "이 ID는 제외됨" 같은 표시가 없음 — 필요해지면 `ExtractResponse`에 `excluded: list[str]` 같은 필드 추가 검토(참조는 됐지만 제외 목록에 걸려 스킵된 것 vs 애초에 참조가 안 된 것을 화면에서 구분하고 싶을 때).
- **실물 회귀 픽스처 대조**: `SPCSP53619C.c`/`SRLGR96602A.c`는 사람이 사진으로 복원한 소스라 일부 구간 저신뢰. `SRLGR96602A.c`는 이번에 `MNT_FUND_INFR_HT_VF016`/`TRU_PBHL_BS_VF501` 죽은 코드를 발견·제거하며 한 차례 검증을 거쳤지만, `SPCSP53619C.c`는 아직 원본과 대조 안 됨 — 여유 있을 때 한 번 더 확인 권장.
