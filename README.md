# No_Gada — Oracle 업무 자동화 툴킷

## 개요

반복 수작업("노가다")을 없애기 위한 **Oracle 전용** 사내 개발자 툴킷. 여러 도구를 좌측 사이드바로
전환하는 **단일 FastAPI 웹 서비스**이며, 각 도구는 백엔드(`app/tools/<name>/`)와 프론트
(`app/static/tools/<name>/`) 한 쌍으로 독립 구성된다. 프론트는 프레임워크 없이 순수 JS.

| 도구 | 기능 | 상태 |
|------|------|------|
| **SQL Bench** | 붙여넣은 Oracle SQL → 참조 물리 테이블 추출 | 구현됨 |
| **Data Migration** | module_type(dbio/service/batch/biz) ID → 원격지(SFTP) 소스 재귀 탐색 → 참조 테이블 추출 → PK 조회 → 이관 DELETE/INSERT 생성 | 구현됨 |
| Impact Analysis | 영향도 분석 | 자리만 확보(준비 중) |

- **테이블 추출 파서**: sqlglot (`dialect="oracle"`) — DB 접속 없이 텍스트 파싱.
- **원격 소스**: 회사 서버가 SFTP라 paramiko 기반. 로컬 검증은 Docker SFTP로 리허설.
- **데이터 조회 DB**: SQLAlchemy `Engine` 기반이라 dialect env 하나로 전환. 기본값은 로컬 Docker Oracle(`all_tables` = 테이블→PK 컬럼 딕셔너리, 실제 반입 대상과 방언 일치), MySQL 리허설로도 전환 가능.

아키텍처 상세는 [`CLAUDE.md`](./CLAUDE.md) 참고.

### 예시
<img width="1666" height="1346" alt="KakaoTalk_Photo_2026-08-09-18-41-45 002" src="https://github.com/user-attachments/assets/919ef774-5dcc-4700-b9e1-fb596eb637eb" />
<img width="1634" height="1330" alt="KakaoTalk_Photo_2026-08-09-18-41-44 001" src="https://github.com/user-attachments/assets/b4b7d3bf-2337-45d8-8791-2afd661c440f" />



## 빠른 시작

**요구사항**: Python 3.9+

```bash
# 1. 가상환경 + 의존성
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. 로컬 개발 env (python-dotenv가 app/main.py 기동 시 자동 로드)
cp .env.example .env

# 3. 개발 서버 (http://localhost:8000)
uvicorn app.main:app --reload

# 4. 전체 테스트 (네트워크 없이 인메모리 fake로 통과)
pytest
pytest tests/tools/test_migrate.py -k group   # 단일 파일/필터 예시
```

**Data Migration 수동 검증용 로컬 서버**(Docker) — 브라우저/`curl` 확인 시에만 필요, `pytest`엔 불필요:

```bash
(cd remote_ssh_server && docker compose up -d --build)  # SSH+SFTP 127.0.0.1:2222  testuser/testpass
pip install -e ".[oracle]"                          # oracledb 드라이버(기본 설치엔 없음)
(cd remote_oracle_server && docker compose up -d)   # Oracle  127.0.0.1:1521  testuser/testpass, service_name=NOGADA (기본 대상)
(cd remote_db_server && docker compose up -d)       # MySQL   127.0.0.1:3306  testuser/testpass, DB=nogada (대안 리허설)
# 정지: docker compose down   /  DB 초기화(init 재실행): docker compose down -v
```

접속 정보는 `.env`(`NOGADA_SFTP_*` / `NOGADA_DB_*`)로 덮어쓸 수 있다 — 코드 하드코딩 기본값은 Oracle(1521)이고, `.env.example`을 그대로 복사하면 MySQL(3306) 블록이 활성화된다.

## 처리 파이프라인

### 공용 테이블 추출 — `app/common/parse/sql.py` `extract_tables(sql) -> list[str]`
`sql_bench`와 `data_migration`가 공유하는 상태 없는 함수.

```
원본 SQL
  ↓ sanitize_text()      보이지 않는 유니코드(BOM·제로폭·NBSP) 제거/정규화
  ↓ strip_db_links()     "테이블 @ 링크"의 @dblink 텍스트 제거(문자열·주석 내 @ 는 보존)
  ↓ sqlglot.parse(oracle)  ;로 나뉜 다중 문장 지원
  ↓ exp.Table 순회        대문자화(스키마 프리픽스·db link는 이미 분리/제거)
  ↓ 제외                  CTE alias·DUAL·USER_/ALL_/DBA_/V$/GV$/SYS.  (인라인 뷰 alias는 자동 제외)
  → 중복 제거 → 알파벳 정렬 리스트
```

- **SQL Bench**: 붙여넣은 SQL → `extract_tables`. `POST /sql-bench/extract` (1MB 초과 413, 파싱 오류 400).

### Data Migration — module ID → 이관 SQL
식별자(DBIO ID, 또는 Service/Batch/Biz의 module_type+resource_group+ID)로 원격 파일을 찾아
읽고, 참조를 재귀적으로 따라가며 도달한 모든 DBIO의 SQL에서 테이블을 뽑아 이관 DELETE/INSERT까지
만든다.

```
GET /data-migration/{module_type}/{file_id}                    # dbio (resource_group 없음, 리프)
GET /data-migration/{module_type}/{resource_group}/{file_id}    # service/batch/biz (재귀)
  dbio:
    ↓ dbio.read_dbio_xml()   ID 끝 2글자로 SQLTYPE 검증 → release/dbio/xml/<ID>.xml (SFTP, 평면 배치)
    ↓ dbio_sql.extract_sql()   published XML의 <sqlString> 수집
    ↓ extract_tables()       각 SQL의 참조 테이블 합집합
  service/batch/biz:
    ↓ module_source.read_module_source()  compile/<업무그룹>/src/... 에서 .c 소스 조회
    ↓ c_source.strip_comments()           //, /* */ 주석 제거(죽은 코드 오탐 방지)
    ↓ refs.scan_module_refs()          콜 매크로(pfmDbio*/pfmDlCall/pfmServiceModuleCall)로
                                        참조 dbio/biz/service ID 추출 + batch는 리터럴 패턴 스캔
    ↓ 재귀(순환 차단 visited, config/excluded_refs.txt 로 항상-제외 ID 필터)
       진입 모듈 자신은 소스 조회 성공 시 services/bizs에 self-include(dbio의 self-include와 동일 규칙)
  → {tables, sql, dbios, batches, services, bizs}
    (프론트: 텍스트·접두사 필터·삭제로 대상 좁힘 = 이관 대상. dbios/services/bizs는 "추출경로" 토글로 표시)

POST /data-migration/pks        {tables} → {테이블: [PK컬럼]}   (all_tables 1회 조회, 캐시)
  → 프론트: 대상들의 PK 합집합으로 키 입력란 표시(컬럼명이 date로 끝나면 단일/기간 토글)

POST /data-migration/migrate-sql  {tables, from_link, to_link, keys} → {sql, generated, skipped, no_pk, groups}
  라우터 → service.migrate_sql(정규화 + PK 조회) → migrate.build_migration_sql(순수 함수)
  = 테이블마다  DELETE FROM t@<TO> WHERE ...;  INSERT INTO t@<TO> SELECT * FROM t@<FROM> WHERE ...;
  → 프론트: 접미사 그룹(_BS/_HT/_MA/_SM/_TR/기타)별 박스로 팝업 표시, 미생성 테이블은 사유와 함께 표로
```

에러 매핑: `UnknownSqlType`/`ExtractionError`→400, `resource_group` 누락(service/batch/biz)→400,
`SourceNotFound`→404, `SourceError`(원격 접속)→503, `DbError`→503, `QueryError`→500.

## 프로젝트 구조

```
.
├── app/
│   ├── main.py                     # FastAPI 앱 조립 + load_dotenv() + 로깅 설정
│   ├── common/                     # 툴 횡단 공용 모듈 (io/parse/proframe 3개 서브패키지)
│   │   ├── io/sftp.py              #   SourceReader/SftpSourceReader/default_reader (원격 SFTP I/O)
│   │   ├── io/db.py                #   DbClient/SqlAlchemyDbClient/default_db (원격 DB I/O, 기본 Oracle)
│   │   ├── parse/text_sanitize.py  #   sanitize_text (유니코드 정제)
│   │   ├── parse/sql.py            #   extract_tables / strip_db_links (Oracle 테이블 추출)
│   │   ├── parse/c_source.py       #   strip_comments (C 소스 주석 제거, 문자열 리터럴 보존)
│   │   ├── proframe/types.py       #   Module_Type/ResourceGroup/PROFRAME_ROOT (ProFrame ID 분류 체계)
│   │   ├── proframe/dbio.py        #   read_dbio_xml (DBIO ID → 원격 XML 위치·조회)
│   │   ├── proframe/module_source.py #  read_module_source (service/batch/biz ID → 원격 .c 소스 조회)
│   │   └── proframe/db_schema.py   #   fetch_pk_columns (all_tables → 테이블별 PK 컬럼)
│   ├── tools/
│   │   ├── sql_bench/router.py     # SQL 텍스트 → 테이블
│   │   └── data_migration/        # 라우터 / 오케스트레이션 / 파서 / 이관 SQL 생성(순수)
│   │       ├── router.py  service.py  dbio_sql.py  migrate.py
│   │       ├── refs.py             #   scan_module_refs (.c 소스 → 참조 dbio/biz/service/batch ID)
│   │       └── excludes.py         #   load_excluded_refs (재귀 참조 항상-제외 ID 목록)
│   └── static/                     # UI (프레임워크 없음, 순수 JS)
│       ├── index.html              #   사이드바 + 툴별 page 컨테이너
│       ├── js/app.js               #   nav 전환 + 공용 헬퍼(App.showToast/copyToClipboard)
│       └── css/ , tools/<tool>/    #   공용/툴별 스타일·스크립트
├── tests/
│   ├── common/                     # test_text_sanitize / test_sql / test_csource / test_db / test_schema / test_module_src
│   └── tools/                      # test_sql_bench / test_data_migration / test_migrate / test_refs / test_excludes
├── config/
│   ├── excluded_refs.txt           # 재귀 참조 집계에서 항상 제외할 ID 목록(한 줄에 하나, # 주석)
│   └── module_group_map.txt        # 재귀 중 참조 ID → 업무그룹 사전 매핑(find 폴백 가속용)
├── .env.example                    # NOGADA_* env 템플릿 (.env는 로컬 전용, python-dotenv가 자동 로드)
├── remote_ssh_server/                # 개발용 로컬 SSH+SFTP + 실물 DBIO/모듈 소스 픽스처, 127.0.0.1:2222
├── remote_db_server/                # 개발용 로컬 MySQL(mysql:8.0), 127.0.0.1:3306, all_tables 시드
├── remote_oracle_server/            # 개발용 로컬 Oracle(gvenzl/oracle-free), 127.0.0.1:1521, all_tables 동일 시드(기본 대상)
├── pyproject.toml                  # deps: fastapi/uvicorn/sqlglot/paramiko/SQLAlchemy/PyMySQL/python-dotenv, optional: dev/oracle
└── CLAUDE.md                       # 아키텍처 상세(작업 가이드)
```
