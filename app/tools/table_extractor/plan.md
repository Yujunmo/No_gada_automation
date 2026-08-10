# Table Extractor — 백엔드 (원격 소스 → 참조 테이블 추출)

> **기준:** DBIO 포맷·경로는 실물 픽스처 `remote_server/files/…/release/dbio/xml/`(평면 `<ID>.xml`)를 정답으로 삼는다. *(2026-08-10 실물 경로 정정 — 이전 `publish_ecams/resource/<PROG>/<SQLTYPE>/…`는 오경로였음. 아래 날짜 로그의 옛 경로 서술보다 맨 끝 2026-08-10 섹션이 최신.)*

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
**실물 디렉토리 레이아웃**(`remote_server/files/truap01dap1/proframe/proframe5.0/` 기준):
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
- reader는 env(`NOGADA_SFTP_*`)에서 `SftpSourceReader`로 생성(기본 `remote_server` Docker SFTP 127.0.0.1:2222). 교체 지점 한 곳. → `app/common/source.py`의 `default_reader()`.

### 6. 프론트 연결 (마무리) `app/static/tools/table_extractor/table_extractor.js`
- `#te-submit` 클릭 → `POST /table-extractor/extract {id_type, id}` fetch.
- 성공: 좌측 `.te-empty`를 **테이블 목록**(sql_bench의 `.table-list`/`.table-item` 톤 재사용, 단 table_extractor 자체 스타일)으로 교체, 우측 `#te-sql` textarea에 `sql` 채움.
- 실패: 좌측에 에러 박스(components.css `.error-box`) 표시. 로딩 스피너 재사용.

## 명시적으로 남기는 결정
- **부분 성공**: Service/Batch/Biz 해석 중 개별 DBIO 파싱 실패는 스킵+경고, 나머지 합집합은 반환. 최상위 파일 자체 실패만 4xx.
- XML 매퍼 파서는 table_extractor 전용(현재 유일 사용처)이라 `app/common/`으로 올리지 않는다. 테이블 추출(`extract_tables`)만 공용 재사용.

## 검증 (end-to-end)
1. **단위 테스트** `tests/tools/test_table_extractor.py` (네트워크 無, 인메모리 fake reader 주입):
   - DBIO 단건: `<sqlString>` → 테이블 정확히 추출(`:bind`·힌트·UNION·엔티티 언이스케이프 포함). 픽스처는 `remote_server/files/.../DYNAMICSQL/{PFO_STCK_MA_DS200,PFO_FUND_BS_DF037}`, `.../EXECSQL/PFO_MNCM_CLCD_HT_EI901` 활용(기대: 각각 {PFO_STCK_MA,TRU_STCK_ITMS_HT,PFO_BRWN_STCK_MA,PFO_SPA_MA,PFO_SPA_ITMS_HT} / {PFO_FUND_BS,PFO_TAMI_SM,PFO_CLFD_REVS_STPR_MA} / {PFO_MNCM_CLCD_HT}).
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

# 진행 상황 (2026-08-04 기준 — 내일 이어서)

## ✅ 완료
1. **프론트 화면**: 컨트롤 행(드롭박스[DBIO/Service/Batch/Biz] + 입력 + 추출하기) + 좌우 1:1 워크스페이스(좌=테이블목록 placeholder, 우=`delete insert sql` textarea). `추출하기`는 아직 무동작.
2. **`router.py` 스켈레톤**: `ExtractRequest{id_type: Literal, id}` / `ExtractResponse{tables, sql, dbios}`, `POST /table-extractor/extract`. 빈 id→400, 잘못된 타입→422. **현재 501 반환**(서비스 미구현), 서비스 연결부는 주석으로 대기. TestClient로 상태코드 검증 완료, 앱 정상 부팅.
3. **`app/common/source.py`** (원래 tool에 뒀다가 **common으로 이동** — 도메인 지식 없는 범용 I/O 인프라, text.py와 같은 범주):
   - `SourceReader`(runtime_checkable Protocol, `read(path)->str`)
   - `SourceNotFound`(파일 부재→404) / `SourceError`(접속·인증·전송 실패→후속 502 매핑)
   - `SftpSourceReader`(paramiko 기반, host/port/user/password/base_dir 주입, `read`마다 connect→open_sftp→open/read→decode. 파일 없음→SourceNotFound, 인증/접속 실패→SourceError, 호스트키 `AutoAddPolicy`). 회사 서버 프로토콜이 SFTP라 ftplib이 아니라 paramiko.
   - **`LocalSourceReader`는 삭제함** — 개발/검증은 Docker SFTP, 단위테스트는 인메모리 fake로 대체.
   - `paramiko>=3.0` → pyproject **런타임** deps에 추가. 로거 `no_gada.source`.
4. **Docker SFTP 테스트 환경** (회사 서버 없이 127.0.0.1로 실코드 경로 검증):
   - `remote_server/`(atmoz/sftp): 127.0.0.1:**2222**, 계정 **testuser/testpass**, base=`src`, 픽스처 = `remote_server/files/…/publish_ecams/resource/`.
   - **실접속 검증 완료**: `docker compose up -d` 후 `SftpSourceReader("127.0.0.1", port=2222, user="testuser", password="testpass", base_dir="src")`로 3개 DBIO 픽스처 읽기 성공, 없는 파일→SourceNotFound, 읽은 `<sqlString>`→`extract_tables`→기대 테이블 일치(PFO_STCK_MA_DS200/PFO_FUND_BS_DF037/PFO_MNCM_CLCD_HT_EI901).

## ⏭️ 다음 (내일)
- [ ] **`ids.py`**: 실물 경로 규칙(`publish_ecams/resource/<PROG>/<SQLTYPE>/<ID>/<ID>.xml`) 반영. `resolve_path(id_type, id, reader)`는 DBIO를 트리 탐색으로 위치 결정 / `classify(id)`(접미·패턴) / `scan_ref_ids(text)`. ※ Service/Batch/Biz 규칙은 상위 `.c` 실물 확인 후 확정.
- [ ] **`mapper.py`**: ProFrame DBIO XML → SQL. `ElementTree`로 **`sqlString` 텍스트** 수집(루트 태그 무관), 엔티티/CDATA 해제. **바인드 치환 없음**(이미 `:name`). ※ 픽스처: `remote_server/files/.../{DYNAMICSQL,EXECSQL}/...`.
- [ ] **`source.py` 나열 메서드**: 트리 탐색용 `list`/`glob`를 `SourceReader`에 추가(SFTP `listdir`+fake 구현). ← `resolve_path` DBIO 탐색이 의존.
- [ ] **`service.py`**: `extract(id_type, id, reader)` + 재귀 `_collect`(visited로 순환 차단, dbio 종료 / 그 외 scan→classify→재귀). 수집 SQL 각각 `extract_tables`→합집합. DBIO 파싱 실패는 skip+warning.
- [ ] **`router.py` 연결**: 501 제거, 주석부 활성화. `default_reader()`는 env(`NOGADA_SFTP_HOST`/`_PORT`/`_USER`/`_PASS`/`_BASE`)에서 `SftpSourceReader` 생성(기본 `remote_server` Docker SFTP 127.0.0.1:2222/testuser/testpass/base=src). ※ `app/common/source.py`로 이동됨.
- [ ] **프론트 `#te-submit`** fetch 연결(좌 목록/우 SQL 채움, 에러박스/스피너 재사용).
- [ ] **테스트** `tests/tools/test_table_extractor.py`: 인메모리 fake reader로 단위(재귀/순환/부재/DYNAMICSQL·EXECSQL 루트), Docker SFTP(`remote_server`)로 `SftpSourceReader` 통합.

## ⚠️ 원래 계획 대비 바뀐 점 (위 본문과 상충하는 부분은 이 진행상황이 최신)
- `source.py` 위치: `app/tools/table_extractor/` → **`app/common/source.py`**.
- 소스 reader: `LocalSourceReader` **삭제** → 개발/운영 모두 `SftpSourceReader`(개발은 Docker SFTP), 테스트는 인메모리 fake.
- 라우터 기본 reader: `LocalSourceReader(TE_SOURCE_DIR)` → **`SftpSourceReader`(env, 기본 Docker SFTP 2222)**.

## 🔴 사용자 제공 현황
- ✅ **DBIO 실물 확인 완료**(사진→`remote_server` 픽스처): DYNAMICSQL/EXECSQL 포맷, `<sqlString>` 텍스트, Oracle `:name` 바인드. 경로 = `publish_ecams/resource/<PROG>/<SQLTYPE>/<ID>/<ID>.xml`.
- ⏳ **미제공**: Service/Biz(`.c`) 파일에서 하위 DBIO ID가 박힌 실제 모습 → `classify`/`scan_ref_ids`/Service·Batch 경로 규칙 확정에 필요.

## 실행 메모
```bash
source .venv/bin/activate && pip install -e ".[dev]"       # paramiko 포함
(cd remote_server && docker compose up -d)                  # Docker SFTP (127.0.0.1:2222, testuser/testpass)
# 접속 확인: SftpSourceReader("127.0.0.1", port=2222, user="testuser", password="testpass", base_dir="src").read("truap01dap1/.../PFO_STCK_MA_DS200.xml")
uvicorn app.main:app --reload                               # 웹앱
pytest                                                      # 회귀(현재 72개)
```

---

# 진행 상황 (2026-08-08 기준)

## ✅ DBIO 추출 파이프라인 완료
- **REST 계약 변경**: `POST /table-extractor/extract`(바디) → **`GET /table-extractor/{id_type}/{prog}/{id}`**(경로 파라미터). 부작용 없는 멱등 조회라 GET이 자연스럽고, 세 값 다 짧은 식별자라 URL에 넣는 데 문제없음. `id_type`/`prog` 타입은 `app/common/proframe.py`(`IdType`/`Prog` `Literal`)로 공용화 — ProFrame ID 분류 체계 자체라 다른 툴에서도 재사용될 값. `prog`는 실물 7개(`PCSP PCSH NCOM NCSP PCOM PPFR RLGR`) 전부 반영(화면 콤보박스도 동기화).
- **DBIO 경로 해석 설계가 원래 계획과 달라짐**: `prog`를 사용자가 이미 명시적으로 주므로 트리 전체를 나열할 필요가 없어졌고, 남은 미지수였던 `SQLTYPE`도 **ID 끝 2글자 코드**(`DS200`의 `DS` 등)로 확정됨(`DF/DS/DI/DU/DD`→DYNAMICSQL, `EI/EU/ED`→EXECSQL, `PI/PU/PD/PS/PF`→PERSIST, `VF/VS`→VIEW). 그래서 **`SourceReader.list()/glob()` 추가 없이** `classify_sqltype(id)` 정규식 매칭 → 경로 1회 조합 → `read()` 1회로 끝남. 매칭 안 되는 접미사는 `UnknownSqlType`(→ 400)로 명확히 거부. 처음엔 `app/tools/table_extractor/ids.py`로 만들었다가, "DBIO ID → 원격 XML 읽기"는 다른 툴에서도 소비처가 늘어날 동작이라 **`app/common/dbio.py`로 이동**(모듈명도 더 직관적으로 개명).
- **`mapper.py`**: `ElementTree` + 로컬네임(`sqlString`) 매칭으로 루트 태그/네임스페이스 무관하게 SQL 추출, XML 파싱 실패 시 정규식 폴백. 실물 DYNAMICSQL(네임스페이스 없음)·EXECSQL(루트에 네임스페이스 있고 자식은 `xmlns=""`로 리셋) 둘 다 fixture로 검증.
- **`service.py`**: `extract(id_type, prog, id, reader)` — 지금은 `id_type == "dbio"`만 구현, 그 외는 라우터에서 501. reader 팩토리 `default_reader()`는 **`app/common/source.py`**에 있고 env(`NOGADA_SFTP_HOST/_PORT/_USER/_PASS/_BASE`) 기반, 기본값 Docker SFTP. FastAPI `Depends(default_reader)`로 라우터에 주입해 테스트에서 `app.dependency_overrides`로 인메모리 fake reader 교체 가능.
- **`router.py`**: 501 스텁 제거(DBIO 한정), `UnknownSqlType`→400 / `SourceNotFound`→404 / `ExtractionError`→400 매핑. `id_type != "dbio"`는 여전히 501.
- **테스트**: `tests/tools/test_table_extractor.py` 30개 — `mapper`/`dbio` 순수 함수 단위, 라우터 통합(성공/404/400/422/501/405 전부), 실 Docker SFTP로 `curl`까지 수동 검증 완료(`PFO_STCK_MA_DS200`→기대 테이블 5개 정확히 일치).

## ⏭️ 남은 것
- [ ] Service/Batch/Biz `id_type` 구현 — 상위 `.c` 파일 실물(하위 DBIO ID가 박히는 모습)을 아직 못 봐서 `classify`/`scan_ref_ids`/경로 규칙 미확정. 재귀 해석(`visited`로 순환 차단) 로직도 이때 추가.
- [ ] 프론트 `#te-submit` fetch 연결 — 지금 API가 `GET /table-extractor/{id_type}/{prog}/{id}`이므로 콤보박스/드롭박스/입력값으로 URL 조합해 fetch, 좌측 테이블 목록/우측 SQL 채우기, 에러박스·스피너 재사용.

---

# 진행 상황 (2026-08-10 기준 — DBIO 경로 평면화 + 네이밍 정리)

> **이 섹션이 최신**이다. 위 2026-08-04·08-08 로그의 `publish_ecams/resource/<PROG>/<SQLTYPE>/<ID>/<ID>.xml` 경로, `read_dbio_xml`에 `prog/resource_group` 인자, `IdType`/`Prog` 명칭은 **모두 아래로 대체**됨.

## 🔀 DBIO 실물 경로 정정 — 평면 구조
- 실물 경로는 `publish_ecams/resource/<PROG>/<SQLTYPE>/<ID>/<ID>.xml`이 아니라 **`release/dbio/xml/<ID>.xml`(완전 평면 — PROG·SQLTYPE 하위 없음)**이었다. `remote_server/files/…/`의 DBIO XML 5개(신규 복원 `AIS_ACCSUBJ_BS_VF001` + 기존 `PFO_CLCD_MIP_MA_VF001`·`PFO_FUND_BS_DF037`·`PFO_MNCM_CLCD_HT_EI901`·`PFO_STCK_MA_DS200`)를 이 디렉토리로 이동, 옛 `publish_ecams/` 트리는 제거.
- **`app/common/dbio.py`**:
  - `DBIO_RESOURCE_ROOT` = `/src/truap01dap1/proframe/proframe5.0/release/dbio/xml`.
  - `read_dbio_xml(file_id, reader)` — **`resource_group` 인자 제거**(평면이라 PROG 불필요). 경로 = `{ROOT}/<ID>.xml` 1회 조합.
  - `classify_sqltype(file_id)`는 이제 **경로 결정용이 아니라 접미사 검증 전용**으로 남는다: 인식 못 하는 접미사(`SQL_TYPE_BY_SUFFIX`/`ID_SUFFIX_RE` 미매칭)를 `UnknownSqlType`으로 던져 잘못된 ID를 파일없음(404)보다 명확한 **400**으로 먼저 거른다. (SQLTYPE 매핑 표·정규식은 그대로 유지 — 검증 게이트로 재사용.)
- **`service.py`**: `read_dbio_xml(file_id, reader)` 호출로 수정(`resource_group`은 로그·라우트 계약용으로만 유지).

## 🏷️ 공용 타입·파라미터 네이밍 정리
- `app/common/proframe.py`: **`IdType` → `Module_Type`**, **`Prog` → `ResourceGroup`**(값 집합은 동일: `dbio/service/batch/biz`, `PCSP PCSH NCOM NCSP PCOM PPFR RLGR`).
- `extract`/`read_dbio_xml` 파라미터: **`id_type` → `module_type`**, **`prog` → `resource_group`**, **`id` → `file_id`**.

## 🔗 URL 계약은 그대로 유지
- **`GET /table-extractor/{module_type}/{resource_group}/{file_id}`** 유지. DBIO에선 `resource_group`이 파일 위치 탐색에 쓰이지 않지만, **향후 Service/Batch/Biz 확장 시 `compile/<PROG>/src/{batch,module,serviceModule}/…` 경로 결정에 실제로 사용**할 예정이라 라우트·프론트 계약을 바꾸지 않는다. `module_type`/`resource_group`은 계속 `Literal`이라 잘못된 값은 FastAPI 422.

## ✅ 테스트
- `tests/tools/test_table_extractor.py`: `FIXTURE_ROOT`·기대 경로(`DS200_PATH`/`EI901_PATH`)를 평면으로, `read_dbio_xml` 호출에서 `resource_group` 인자 제거. `classify_sqltype`(→400)·`SourceNotFound`(→404)·`Literal`(→422) 검증은 그대로.
- **전체 103개 통과.**
