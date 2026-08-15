# 재귀적 테이블 추출: Service / Batch / Biz 모듈 지원

**상태: 구현 완료** (2026-08-13 기준, `pytest` 137개 그린). 아래 "설계"는 실제 구현된 최종 형태를 기록한다. 남은 항목은 맨 아래 "미해결 / 후속" 참고.

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

## 파일
- 수정: `app/common/source.py`(+`listdir`, `_connect` 리팩터), `app/common/proframe.py`(+`PROFRAME_ROOT`), `app/common/dbio.py`(`DBIO_RESOURCE_ROOT`를 `PROFRAME_ROOT` 조합으로), `app/tools/table_extractor/service.py`(재귀 분리), `app/tools/table_extractor/router.py`(501 제거·400·503·`batches`), `tests/tools/test_table_extractor.py`.
- 신규: `app/common/csource.py`(C 주석 제거), `app/common/module_src.py`(모듈 위치·조회), `app/tools/table_extractor/refs.py`(참조 스캔), `tests/common/test_csource.py`, `tests/common/test_module_src.py`, `tests/tools/test_refs.py`.
- 문서: 이 파일. `CLAUDE.md`는 아직 미반영(아래 후속 참고).

## 검증
1. **단위/통합**: `pytest tests/tools/test_table_extractor.py tests/tools/test_refs.py tests/common/test_csource.py tests/common/test_module_src.py` — 전부 그린.
2. **전체 회귀**: `pytest` — 137개 그린(2026-08-13 기준).
3. **수동(제한적, 미실시)**: `remote_ap_server` Docker SFTP 기동 후 `GET /table-extractor/biz/PCOM/MPCOM_GetBzopDate` — 실물 biz 소스는 있으나 참조 DBIO XML(VS004~011)이 아직 remote에 없어 nested skip+warn로 부분/빈 결과가 정상. 실 end-to-end는 해당 DBIO XML 픽스처 확보 후.

## 미해결 / 후속
- **`CLAUDE.md` 미반영**: 이번 재귀 파이프라인(`module_src.py`/`refs.py`/`csource.py`/`service.py` 재귀/`PROFRAME_ROOT`/`batches` 필드)이 아직 `CLAUDE.md`의 "Table Extractor 파이프라인" 절에 반영 안 됨.
- **매핑파일 우선탐색**: `module_src.read_module_source`의 find 앞단에 "소스→업무그룹 매핑" 조회 삽입(사용자 준비 시).
- **service `sizeof(_IN)` 정규식**: 실물 샘플이 아직 하나도 없음(보유 픽스처는 전부 `pfmDlCall`만 사용) — `pfmServiceModuleCall` 실물 확보 시 회귀로 검증 필요.
- **프론트엔드 미반영**: `table_extractor.js`가 여전히 DBIO 2세그먼트 전제로만 짜여 있을 수 있음 — service/batch/biz 3세그먼트 호출 + 응답의 새 `batches` 필드 표시(화면 노출) 반영 필요.
- **실물 회귀 픽스처**: `SPCSP53619C.c`/`SRLGR96602A.c`는 사람이 사진으로 복원한 소스라 일부 구간 저신뢰 — 이번에 실제 테스트 픽스처로 채택됐으니(`test_refs.py`, `test_table_extractor.py`) 원본과 대조 여유 있을 때 한 번 더 검증 권장.
