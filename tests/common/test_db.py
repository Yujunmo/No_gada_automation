"""
app/common/io/db.py 단위 테스트.

io/sftp.py와 마찬가지로 실제 접속 구현(MySqlDbClient)은 네트워크가 필요하므로 라이브 검증하지 않는다.
여기서는 네트워크 없이 확인 가능한 것만 고정한다:
  - default_db() 팩토리가 env(NOGADA_DB_*)를 정확히 반영하는지
  - 인메모리 가짜 client가 DbClient Protocol을 만족하는지(runtime_checkable)
  - 에러 매핑용 예외(DbError/QueryError)가 구분되는지
"""
from __future__ import annotations

import pytest

from app.common.io.db import DbClient, DbError, MySqlDbClient, Params, QueryError, Row, default_db


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
    for k in ("NOGADA_DB_HOST", "NOGADA_DB_PORT", "NOGADA_DB_USER", "NOGADA_DB_PASS", "NOGADA_DB_NAME"):
        monkeypatch.delenv(k, raising=False)
    db = default_db()
    assert isinstance(db, MySqlDbClient)
    assert (db._host, db._port, db._user, db._database) == ("127.0.0.1", 3306, "testuser", "nogada")


def test_default_db_reads_env(monkeypatch):
    monkeypatch.setenv("NOGADA_DB_HOST", "db.corp.local")
    monkeypatch.setenv("NOGADA_DB_PORT", "1521")
    monkeypatch.setenv("NOGADA_DB_USER", "app")
    monkeypatch.setenv("NOGADA_DB_PASS", "secret")
    monkeypatch.setenv("NOGADA_DB_NAME", "PROD")
    db = default_db()
    assert (db._host, db._port, db._user, db._database) == ("db.corp.local", 1521, "app", "PROD")
    assert db._password == "secret"
