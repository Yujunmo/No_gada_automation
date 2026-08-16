# 재귀적 테이블 추출: Service / Batch / Biz 모듈 지원

**상태: 구현 완료 + 후속 확장 반영** (2026-08-16 기준, `pytest` 154개 그린). 아래 "설계"는 실제 구현된 최종 형태를 기록한다. 남은 항목은 맨 아래 "미해결 / 후속" 참고.

**2026-08-13 이후 추가된 것**(이 문서 최초 작성 이후):
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
- 문서: 이 파일. `CLAUDE.md`는 "재귀 참조 제외 목록" 절만 반영됐고, 재귀 파이프라인 자체(라우터 흐름 서술)는 아직 미반영(아래 후속 참고).

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
