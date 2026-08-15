# 테스트용 MySQL DB 서버

노가다 앱이 **데이터를 조회해오는 대상 DB**를 로컬에서 리허설하는 서버(Docker MySQL 8).
실제 반입 시에는 회사 서버(Oracle)에 붙지만, 용도가 **단순 조회**라 방언 차이가 없어 테스트는
MySQL로 갈음한다. 앱은 드라이버/접속정보만 교체하면 된다(`remote_ap_server`의 SFTP `SourceReader`와 동일한 구조).

## 접속 정보

| 항목 | 값 |
|------|-----|
| host | `127.0.0.1` |
| port | `3306` |
| user | `testuser` |
| password | `testpass` |
| database | `nogada` |
| root password | `rootpass` (관리용) |

> 앱 쪽 접속 팩토리(`default_db()` 등)가 이 값을 `NOGADA_DB_*` 환경변수 기본값으로 그대로 쓸 예정.
> (SFTP의 `NOGADA_SFTP_*`와 같은 규약: `NOGADA_DB_HOST/_PORT/_USER/_PASS/_NAME`)

## 스키마 / 시드

`init/` 아래 `*.sql`이 **최초 기동 시** 알파벳 순으로 자동 실행된다(볼륨이 비어 있을 때만).

```
init/
  01_all_tables.sql  all_tables(table_id → pk_column 매핑, PK 없음)
```

- **`all_tables`**: 테이블명(`table_id`) → PK 컬럼명(`pk_column`) 매핑. 복합키 테이블은 한 테이블당
  여러 행을 가지므로 PK 제약이 없다. 예: `SELECT pk_column FROM all_tables WHERE table_id='PFO_STCK_MA'`.

스키마/데이터를 바꾸고 다시 반영하려면 볼륨을 초기화해야 한다(아래 `down -v`).

## 사용법

```bash
cd remote_db_server
docker compose up -d          # 기동 (최초엔 init/*.sql 실행)
docker compose ps             # 상태/health 확인
docker compose logs -f mysql  # 로그
docker compose down           # 정지 (데이터 유지)
docker compose down -v        # 정지 + 볼륨 삭제 (다음 기동 시 init/ 재실행 = 완전 초기화)
```

## 수동 접속 확인

```bash
# 컨테이너 내부 mysql 클라이언트로 바로 확인 (호스트에 mysql 미설치여도 됨)
docker compose exec mysql mysql -utestuser -ptestpass nogada -e "SELECT * FROM all_tables;"
docker exec -it remote_db_server-mysql-1 /bin/sh
mysql -utestuser -ptestpass nogada

# 호스트에 mysql 클라이언트가 있으면
mysql -h 127.0.0.1 -P 3306 -utestuser -ptestpass nogada
```

> **초기화 주의**: `init/*.sql`은 데이터 볼륨(`mysql_data`)이 비어 있는 **최초 기동에만** 실행된다.
> 이미 기동한 적이 있으면 `init/`를 고쳐도 반영되지 않으니 `docker compose down -v` 후 다시 올려야 한다.
