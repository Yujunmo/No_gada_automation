"""
app/common/io/db.py 단위 테스트.

io/sftp.py와 마찬가지로 실제 접속 구현(SqlAlchemyDbClient)은 네트워크가 필요하므로 라이브 검증하지 않는다.
여기서는 네트워크 없이 확인 가능한 것만 고정한다:
  - default_db() 팩토리가 env(NOGADA_DB_*)를 정확히 반영하는지(dialect 포함)
  - 인메모리 가짜 client가 DbClient Protocol을 만족하는지(runtime_checkable)
  - 에러 매핑용 예외(DbError/QueryError)가 구분되는지
"""
from __future__ import annotations

from app.common.io.db import (
    DbClient,
    DbError,
    Params,
    QueryError,
    Row,
    SqlAlchemyDbClient,
    _build_url_from_env,
    default_db,
)


class FakeDb:
    """DbClient Protocol을 만족하는 인메모리 가짜 — 툴 테스트에서 dependency_overrides로 주입."""

    def __init__(self, rows: list[Row]):
        self._rows = rows
        self.calls: list[tuple[str, Params]] = []

    def query(self, sql: str, params: Params = None) -> list[Row]:
        self.calls.append((sql, params))
        return self._rows


def test_fake_satisfies_protocol():
    fake = FakeDb([{"n": 1}])
    assert isinstance(fake, DbClient)


def test_fake_query_records_and_returns():
    fake = FakeDb([{"id": 1}, {"id": 2}])
    out = fake.query("SELECT id FROM t WHERE x=%s", (7,))
    assert out == [{"id": 1}, {"id": 2}]
    assert fake.calls == [("SELECT id FROM t WHERE x=%s", (7,))]


def test_errors_are_distinct():
    assert not issubclass(DbError, QueryError)
    assert not issubclass(QueryError, DbError)


def test_default_db_uses_defaults(monkeypatch):
    # 기본값은 로컬 Docker Oracle 리허설(remote_oracle_server) — 실제 반입 대상과 방언을 맞춘다.
    for k in ("NOGADA_DB_HOST", "NOGADA_DB_PORT", "NOGADA_DB_USER", "NOGADA_DB_PASS", "NOGADA_DB_NAME", "NOGADA_DB_DIALECT"):
        monkeypatch.delenv(k, raising=False)
    db = default_db()
    assert isinstance(db, SqlAlchemyDbClient)
    url = db._engine.url
    assert (url.drivername, url.host, url.port, url.username, url.database) == (
        "oracle+oracledb", "127.0.0.1", 1521, "testuser", None,
    )
    assert url.query.get("service_name") == "NOGADA"


def test_default_db_reads_env(monkeypatch):
    # dialect는 이 테스트가 건드리지 않는 유일한 변수라 기본값(oracle+oracledb)을 가정한다 —
    # 개발 환경의 .env가 NOGADA_DB_DIALECT를 설정해뒀다면 그 값이 새어 들어와 실패할 수 있으므로 명시적으로 지운다.
    monkeypatch.delenv("NOGADA_DB_DIALECT", raising=False)
    monkeypatch.setenv("NOGADA_DB_HOST", "db.corp.local")
    monkeypatch.setenv("NOGADA_DB_PORT", "1521")
    monkeypatch.setenv("NOGADA_DB_USER", "app")
    monkeypatch.setenv("NOGADA_DB_PASS", "secret")
    monkeypatch.setenv("NOGADA_DB_NAME", "PROD")
    db = default_db()
    url = db._engine.url
    assert (url.drivername, url.host, url.port, url.username, url.database) == (
        "oracle+oracledb", "db.corp.local", 1521, "app", None,
    )
    assert url.query.get("service_name") == "PROD"
    assert url.password == "secret"


def test_default_db_dialect_switch_is_env_only(monkeypatch):
    # 기본값이 Oracle로 바뀐 뒤에도, MySQL 리허설(remote_db_server)로 되돌리는 게 드라이버 설치
    # 여부와 무관하게 env 값만으로 이뤄지는지 확인.
    # (Engine 생성은 dialect의 DBAPI를 즉시 import하므로, URL 조립만 떼어 검증한다.)
    monkeypatch.setenv("NOGADA_DB_DIALECT", "mysql+pymysql")
    url = _build_url_from_env()
    assert url.drivername == "mysql+pymysql"


def test_default_db_oracle_uses_service_name(monkeypatch):
    # remote_oracle_server(gvenzl/oracle-free)로 실측: database=를 SID로 해석해 접속 실패했음
    # ("SID ... is not registered with the listener") — PDB는 service_name으로 접속해야 한다.
    monkeypatch.setenv("NOGADA_DB_DIALECT", "oracle+oracledb")
    monkeypatch.setenv("NOGADA_DB_HOST", "127.0.0.1")
    monkeypatch.setenv("NOGADA_DB_PORT", "1521")
    monkeypatch.setenv("NOGADA_DB_USER", "testuser")
    monkeypatch.setenv("NOGADA_DB_PASS", "testpass")
    monkeypatch.setenv("NOGADA_DB_NAME", "NOGADA")
    url = _build_url_from_env()
    assert url.database is None
    assert url.query.get("service_name") == "NOGADA"
    assert url.render_as_string(hide_password=False) == (
        "oracle+oracledb://testuser:testpass@127.0.0.1:1521?service_name=NOGADA"
    )
