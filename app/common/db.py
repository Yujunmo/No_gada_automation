"""원격 DB 조회 추상화 (툴 공용 I/O 인프라).

"SQL을 주면 결과 행(list[dict])을 돌려준다"는 한 가지 동작만 제공한다.
`DbClient` 인터페이스 뒤에 `MySqlDbClient`(실제 접속) 구현을 숨긴다. 개발/검증은
로컬 Docker MySQL(`remote_db_server/`, 127.0.0.1:3306)로, 단위 테스트는 인메모리 가짜 client로
이 인터페이스를 만족시킨다. 특정 도구 지식이 없는 범용 인프라라 `app/common/`에 둔다(같은 범주: source.py).

실제 반입 대상은 회사 Oracle이지만 용도가 **단순 조회**라 방언 차이가 없다는 전제다. 따라서 이 모듈은
방언 변환을 하지 않고 순수 I/O + 테스트 주입용 경계일 뿐이다. 반입 후에는 `MySqlDbClient`를
같은 `DbClient` 인터페이스를 만족하는 Oracle 구현(예: oracledb 기반)으로 교체하고 접속 정보만 바꾸면 된다.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional, Protocol, Sequence, Union, runtime_checkable

import pymysql
import pymysql.cursors

logger = logging.getLogger("no_gada.db")

# query params: 위치 바인드(seq) 또는 이름 바인드(dict) 둘 다 허용(드라이버가 해석).
# (런타임 평가되는 별칭이라 PEP 604 '|' 대신 Union — requires-python >=3.9 호환)
Params = Optional[Union[Sequence[Any], dict[str, Any]]]
Row = dict[str, Any]


class DbError(Exception):
    """DB 접근 자체가 실패(접속/인증 오류 등). SQL 실행 실패(QueryError)와 구분."""


class QueryError(Exception):
    """SQL 실행 실패(문법 오류·없는 테이블·제약 위반 등). 접속 실패(DbError)와 구분."""


@runtime_checkable
class DbClient(Protocol):
    """SQL → 결과 행 목록(list[dict]). 접속 실패면 DbError, 실행 실패면 QueryError."""

    def query(self, sql: str, params: Params = None) -> list[Row]: ...


class MySqlDbClient:
    """MySQL 서버를 조회 대상으로 쓰는 client.

    접속 정보는 생성 시 주입한다(호출부가 환경변수에서 읽어 넘김 → 코드/깃에 비밀 없음).
    `query`마다 접속/해제하는 단순 모델(상태 없는 세션) — source.py의 SftpSourceReader와 동일한 방침.
    결과는 `DictCursor`로 컬럼명→값 dict 행 리스트로 돌려준다.

    읽기 전용 용도라 커밋하지 않는다(SELECT/딕셔너리 조회 전용).
    """

    def __init__(
        self,
        host: str,
        *,
        port: int = 3306,
        user: str,
        password: str | None = None,
        database: str,
        charset: str = "utf8mb4",
        timeout: int = 10,
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database
        self._charset = charset
        self._timeout = timeout

    def query(self, sql: str, params: Params = None) -> list[Row]:
        """접속 후 SQL을 실행하고 결과 행을 list[dict]로 돌려준다."""
        try:
            conn = pymysql.connect(
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                database=self._database,
                charset=self._charset,
                connect_timeout=self._timeout,
                read_timeout=self._timeout,
                cursorclass=pymysql.cursors.DictCursor,
            )
        except pymysql.err.OperationalError as e:
            # 접속/인증/네트워크 계열 → DbError
            raise DbError(f"DB 접속 실패: {self._user}@{self._host}:{self._port}/{self._database} ({e})") from e

        try:
            with conn.cursor() as cur:
                try:
                    cur.execute(sql, params)
                    rows = cur.fetchall()
                except pymysql.err.MySQLError as e:
                    # 문법 오류·없는 테이블 등 실행 실패 → QueryError
                    raise QueryError(f"SQL 실행 실패: {e}") from e
        finally:
            conn.close()

        result = list(rows)
        logger.debug("MySqlDbClient query: %d rows | %.120s", len(result), sql.replace("\n", " "))
        return result


def default_db() -> DbClient:
    """env(NOGADA_DB_*)에서 MySqlDbClient 생성. 기본값은 로컬 Docker MySQL 테스트 서버.

    테스트 DB는 하나뿐이라 여러 툴이 이 팩토리를 공유한다. 라우터에 FastAPI
    `Depends(default_db)`로 주입하면 테스트에서 `app.dependency_overrides`로 교체 가능
    (source.py의 default_reader와 동일한 규약).
    """
    host = os.environ.get("NOGADA_DB_HOST", "127.0.0.1")
    port = int(os.environ.get("NOGADA_DB_PORT", "3306"))
    user = os.environ.get("NOGADA_DB_USER", "testuser")
    database = os.environ.get("NOGADA_DB_NAME", "nogada")
    logger.debug("default_db: MySQL client 생성 %s@%s:%d/%s", user, host, port, database)

    return MySqlDbClient(
        host,
        port=port,
        user=user,
        password=os.environ.get("NOGADA_DB_PASS", "testpass"),
        database=database,
    )
