"""원격 DB 조회 추상화 (툴 공용 I/O 인프라).

"SQL을 주면 결과 행(list[dict])을 돌려준다"는 한 가지 동작만 제공한다.
`DbClient` 인터페이스 뒤에 SQLAlchemy `Engine` 기반 `SqlAlchemyDbClient`를 숨긴다. 개발/검증은
로컬 Docker MySQL(`remote_db_server/`, 127.0.0.1:3306)로, 단위 테스트는 인메모리 가짜 client로
이 인터페이스를 만족시킨다. 특정 도구 지식이 없는 범용 인프라라 `app/common/`에 둔다(같은 범주: source.py).

실제 반입 대상은 회사 Oracle이다. SQLAlchemy Engine을 쓰는 이유는 방언(dialect)별 paramstyle
차이(MySQL `%s` vs Oracle `:name`)를 흡수하기 위함 — 호출부(`db_schema.py` 등)는 항상 named bind
(`:col`)로 SQL을 쓰고, `NOGADA_DB_DIALECT` env(URL scheme)만 바꾸면 실제 드라이버가 교체된다.
비즈니스 로직 쪽 SQL 문자열은 그대로 둔 채 설정만으로 DB를 전환하는 것이 목표라, ORM은 쓰지 않고
SQLAlchemy Core(`text()`)만 사용한다.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional, Protocol, Sequence, Union, runtime_checkable

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

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


class SqlAlchemyDbClient:
    """SQLAlchemy `Engine`으로 여러 DB 방언에 걸쳐 동작하는 client.

    `query`마다 접속/해제하는 단순 모델(상태 없는 세션)은 유지하되, Engine 자체(및 그 안의
    connection pool)는 재사용한다 — source.py의 SftpSourceReader와 동일한 "요청마다 접속" 방침이며,
    Engine 재사용은 SQLAlchemy의 기본 동작일 뿐 별도 세션 상태를 두는 것은 아니다.

    `params`가 dict이고 값이 list/tuple인 항목은 `IN` 절 확장(`bindparam(expanding=True)`)으로
    자동 처리한다 — 호출부는 `"... IN :tables"` + `{"tables": [...]}`만 넘기면 되고, `%s` placeholder를
    개수만큼 직접 join할 필요가 없다.

    결과는 컬럼명→값 dict 행 리스트로 돌려준다. 읽기 전용 용도라 커밋하지 않는다.
    """

    def __init__(self, url: URL | str) -> None:
        self._engine = create_engine(url)

    def query(self, sql: str, params: Params = None) -> list[Row]:
        """접속 후 SQL을 실행하고 결과 행을 list[dict]로 돌려준다."""
        stmt = text(sql)
        if isinstance(params, dict):
            expanding_names = [name for name, value in params.items() if isinstance(value, (list, tuple))]
            if expanding_names:
                stmt = stmt.bindparams(*(bindparam(name, expanding=True) for name in expanding_names))

        try:
            conn = self._engine.connect()
        except SQLAlchemyError as e:
            url = self._engine.url.render_as_string(hide_password=True)
            raise DbError(f"DB 접속 실패: {url} ({e})") from e

        try:
            try:
                result = conn.execute(stmt, params or {})
                rows = [dict(row) for row in result.mappings()]
            except SQLAlchemyError as e:
                raise QueryError(f"SQL 실행 실패: {e}") from e
        finally:
            conn.close()

        logger.debug("SqlAlchemyDbClient query: %d rows | %.120s", len(rows), sql.replace("\n", " "))
        return rows


def _build_url_from_env() -> URL:
    """env(NOGADA_DB_*)에서 SQLAlchemy 접속 URL을 조립한다(순수, Engine 생성 없음).
    Oracle은 service_name을 쓴다. MySQL은 database를 쓴다. dialect는 env(NOGADA_DB_DIALECT)로 결정한다.,
    """
    host = os.environ.get("NOGADA_DB_HOST", "127.0.0.1")
    port = int(os.environ.get("NOGADA_DB_PORT", "1521"))
    user = os.environ.get("NOGADA_DB_USER", "testuser")
    password = os.environ.get("NOGADA_DB_PASS", "testpass")
    database = os.environ.get("NOGADA_DB_NAME", "NOGADA")
    dialect = os.environ.get("NOGADA_DB_DIALECT", "oracle+oracledb")
    logger.debug("_build_url_from_env: %s 조립 %s@%s:%d/%s", dialect, user, host, port, database)

    if dialect.startswith("oracle"):
        return URL.create(
            dialect,
            username=user,
            password=password,
            host=host,
            port=port,
            query={"service_name": database},
        )

    return URL.create(
        dialect,
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def default_db() -> DbClient:
    
    return SqlAlchemyDbClient(_build_url_from_env())
