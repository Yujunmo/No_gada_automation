"""
app/common/io/ssh.py 단위 테스트.

io/sftp.py와 마찬가지로 실제 접속(SshConnection)은 네트워크가 필요하므로 라이브 검증하지
않는다. 여기서는 네트워크 없이 확인 가능한 것만 고정한다: default_command_runner() 팩토리가
env(NOGADA_SFTP_*, NOGADA_SOURCE_ENCODING — SFTP reader와 같은 서버·같은 env를 공유)를
정확히 반영하는지. 생성자는 접속을 시도하지 않으므로(첫 run에서 지연 접속) 네트워크 없이 안전.
"""
from __future__ import annotations

from app.common.io.ssh import SshCommandRunner, default_command_runner


def _build(monkeypatch, **env):
    for k in ("NOGADA_SFTP_HOST", "NOGADA_SFTP_PORT", "NOGADA_SFTP_USER", "NOGADA_SFTP_PASS",
              "NOGADA_SOURCE_ENCODING"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    gen = default_command_runner()
    runner = next(gen)
    return runner, gen


def test_default_command_runner_uses_defaults(monkeypatch):
    runner, gen = _build(monkeypatch)
    assert isinstance(runner, SshCommandRunner)
    assert runner._encoding == "utf-8"
    assert (runner._conn._host, runner._conn._port, runner._conn._user) == ("127.0.0.1", 2222, "testuser")
    gen.close()


def test_default_command_runner_reads_sftp_env(monkeypatch):
    # 별도 NOGADA_SSH_*가 없다 — SFTP와 같은 회사 서버라 NOGADA_SFTP_*를 그대로 재사용한다.
    runner, gen = _build(
        monkeypatch,
        NOGADA_SFTP_HOST="ap.corp.local",
        NOGADA_SFTP_PORT="22",
        NOGADA_SFTP_USER="deploy",
    )
    assert (runner._conn._host, runner._conn._port, runner._conn._user) == ("ap.corp.local", 22, "deploy")
    gen.close()


def test_default_command_runner_source_encoding_overridable(monkeypatch):
    # SFTP reader와 같은 env를 공유(같은 서버는 같은 인코딩이라는 전제).
    runner, gen = _build(monkeypatch, NOGADA_SOURCE_ENCODING="euc-kr")
    assert runner._encoding == "euc-kr"
    gen.close()
