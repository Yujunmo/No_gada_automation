# 테스트용 Oracle DB 서버

`remote_db_server`(MySQL 리허설)와 동일한 시드 데이터로 **실제 Oracle**을 대상으로도 앱의 DB 레이어
(`app/common/io/db.py`)를 검증하기 위한 로컬 리허설 서버(Docker `gvenzl/oracle-free`).
회사 반입 전에 `NOGADA_DB_DIALECT=oracle+oracledb`로 바꿨을 때 코드 변경 없이 그대로 동작하는지
확인하는 용도 — 회사 계정/라이선스 동의가 필요 없는 커뮤니티 유지보수 이미지를 사용한다.

## 접속 정보

| 항목 | 값 |
|------|-----|
| host | `127.0.0.1` |
| port | `1521` |
| user | `testuser` |
| password | `testpass` |
| service_name (database) | `NOGADA` |
| SYS/SYSTEM password | `rootpass` (관리용) |

> `NOGADA_DB_*` 환경변수로 앱을 이 서버에 붙이려면:
> ```bash
> export NOGADA_DB_HOST=127.0.0.1
> export NOGADA_DB_PORT=1521
> export NOGADA_DB_USER=testuser
> export NOGADA_DB_PASS=testpass
> export NOGADA_DB_NAME=NOGADA
> export NOGADA_DB_DIALECT=oracle+oracledb
> ```
> `oracledb` 드라이버는 기본 설치에 없으므로 `pip install -e ".[oracle]"`로 먼저 설치해야 한다.

## 스키마 / 시드

`init/` 아래 `*.sql`이 **최초 기동 시**(볼륨이 비어 있을 때만) SYS 계정으로 SQL*Plus를 통해 알파벳 순 실행된다.

```
init/
  01_all_tables.sql   all_tables(table_id → pk_column 매핑, PK 없음) — remote_db_server와 동일 시드
```

- 스크립트는 `ALTER SESSION SET CONTAINER = NOGADA;` 로 PDB에 진입한 뒤
  `ALTER SESSION SET CURRENT_SCHEMA = TESTUSER;` 로 `testuser` 스키마에 테이블을 만든다
  (MySQL의 `MYSQL_DATABASE`/`MYSQL_USER` 자동 권한 부여와 달리 Oracle은 스키마 전환을 명시해야 함).
- **`all_tables`**: 테이블명(`table_id`) → PK 컬럼명(`pk_column`) 매핑. 복합키 테이블은 한 테이블당
  여러 행을 가지므로 PK 제약이 없다. 예: `SELECT pk_column FROM all_tables WHERE table_id='PFO_STCK_MA'`.

스키마/데이터를 바꾸고 다시 반영하려면 볼륨을 초기화해야 한다(아래 `down -v`).

## 사용법

```bash
cd remote_oracle_server
docker compose up -d           # 기동 (최초엔 init/*.sql 실행, healthy까지 1~2분 소요)
docker compose ps              # 상태/health 확인
docker compose logs -f oracle  # 로그 (init 스크립트 실행 결과 포함)
docker compose down            # 정지 (데이터 유지)
docker compose down -v         # 정지 + 볼륨 삭제 (다음 기동 시 init/ 재실행 = 완전 초기화)
```

## 수동 접속 확인

```bash
# 컨테이너 내부 sqlplus로 바로 확인 (호스트에 Oracle 클라이언트 미설치여도 됨)
docker compose exec oracle sqlplus testuser/testpass@//localhost:1521/NOGADA
docker exec -it remote_oracle_server-oracle-1 /bin/bash

SQL> SELECT * FROM all_tables WHERE table_id = 'PFO_STCK_MA';
```

> **초기화 주의**: `init/*.sql`은 데이터 볼륨(`oracle_data`)이 비어 있는 **최초 기동에만** 실행된다.
> 이미 기동한 적이 있으면 `init/`를 고쳐도 반영되지 않으니 `docker compose down -v` 후 다시 올려야 한다.

## 앱 검증 예시

```bash
pip install -e ".[oracle]"
# 위 NOGADA_DB_* env를 export한 상태에서
uvicorn app.main:app --reload

curl -X POST localhost:8000/table-extractor/pks \
  -H "Content-Type: application/json" \
  -d '{"tables":["PFO_STCK_MA"]}'
# → remote_db_server(MySQL)로 같은 요청했을 때와 동일한 PK 컬럼이 반환되어야 정상
```
