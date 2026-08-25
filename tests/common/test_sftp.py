"""
app/common/io/sftp.py 단위 테스트.

io/db.py와 마찬가지로 실제 접속(SftpSourceReader)은 네트워크가 필요하므로 라이브 검증하지
않는다. 여기서는 네트워크 없이 확인 가능한 것만 고정한다: default_reader() 팩토리가
env(NOGADA_SFTP_*, NOGADA_SOURCE_ENCODING)를 정확히 반영해 SftpSourceReader를 조립하는지.
생성자는 접속을 시도하지 않으므로(첫 read/listdir에서 지연 접속) 네트워크 없이 안전하게 확인 가능.
"""
from __future__ import annotations

from app.common.io.sftp import SftpSourceReader, default_reader


def _build(monkeypatch, **env):
    for k in ("NOGADA_SFTP_HOST", "NOGADA_SFTP_PORT", "NOGADA_SFTP_USER", "NOGADA_SFTP_PASS",
              "NOGADA_SFTP_BASE", "NOGADA_SOURCE_ENCODING"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    gen = default_reader()
    reader = next(gen)
    return reader, gen


def test_default_reader_uses_defaults(monkeypatch):
    reader, gen = _build(monkeypatch)
    assert isinstance(reader, SftpSourceReader)
    assert (reader._host, reader._port, reader._user, reader._base, reader._encoding) == (
        "127.0.0.1", 2222, "testuser", "src", "utf-8",
    )
    gen.close()


def test_default_reader_reads_env(monkeypatch):
    reader, gen = _build(
        monkeypatch,
        NOGADA_SFTP_HOST="ap.corp.local",
        NOGADA_SFTP_PORT="22",
        NOGADA_SFTP_USER="deploy",
        NOGADA_SFTP_BASE="release",
    )
    assert (reader._host, reader._port, reader._user, reader._base) == (
        "ap.corp.local", 22, "deploy", "release",
    )
    gen.close()


def test_default_reader_source_encoding_overridable(monkeypatch):
    # 회사 서버가 UTF-8이 아니면(EUC-KR/CP949 등) 이 env로 전환한다.
    reader, gen = _build(monkeypatch, NOGADA_SOURCE_ENCODING="cp949")
    assert reader._encoding == "cp949"
    gen.close()
