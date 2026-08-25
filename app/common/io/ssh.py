"""원격 SSH 명령 실행 추상화 (툴 공용 I/O 인프라).

`io/sftp.py`가 "경로 → 파일 내용"이라는 파일 접근을 담당한다면, 이 파일은 "명령 →
실행 결과(stdout/stderr/exit code)"라는 **원격 셸 실행**을 담당한다. 회사 서버가 SSH라
파일 전송(SFTP 서브시스템)과 명령 실행(SSH exec)이 **같은 SSH 연결 위**에 얹히므로,
핸드셰이크 비용을 아끼려 `SshConnection`(연결 수명 관리) 하나를 두 쪽이 공유하도록
설계했다(현재는 이 파일이 자체 연결을 맺지만, 추후 `SftpSourceReader`도 `SshConnection`을
주입받게 리팩터하면 요청당 세션 1개로 통합 가능).

성장은 **클래스가 아니라 함수로** 한다. `SshCommandRunner`는 `run(argv)` 하나만 가진
얇은 원시(primitive)로 고정하고, grep·find·wc 같은 구체 기능은 이 원시 위에 얹은
**순수 조합 함수**로 축적한다(첫 기능이 `grep_files`). 이러면 기능이 늘어도 클래스/Protocol은
안 바뀌고, 테스트 fake는 `run` 하나만 구현하면 모든 기능을 커버한다.
"""
from __future__ import annotations

import logging
import os
import shlex
from dataclasses import dataclass
from typing import Iterator, Protocol, runtime_checkable

import paramiko

logger = logging.getLogger("no_gada.ssh")


class SshError(Exception):
    """SSH 접속/명령 실행 자체가 실패(접속·인증·전송 오류, 비정상 종료 등)."""


@dataclass(frozen=True)
class CommandResult:
    """원격 명령 1건의 실행 결과.

    exit_code는 명령의 종료 코드를 그대로 담는다(호출부가 의미를 해석) — 예: grep은
    "매칭 없음"을 1로 내는데 이는 정상 상황이지 에러가 아니므로, 실행 실패(SshError)와
    구분해 조합 함수가 판단한다.
    """

    stdout: str
    stderr: str
    exit_code: int


@runtime_checkable
class CommandRunner(Protocol):
    """argv → CommandResult. 얇은 원시 하나로 고정(기능은 이 위에 함수로 조합)."""

    def run(self, argv: list[str], *, timeout: int | None = None) -> CommandResult: ...


class SshConnection:
    """SSH 세션 수명 관리(맺기/재사용/재접속/닫기)를 한 곳에 모은 객체.

    SFTP 읽기와 SSH 명령 실행이 같은 서버로 붙으므로, 이 연결 하나를 공유해 핸드셰이크
    비용을 없앤다(재귀 추출·다중 grep이 같은 연결로 수십~수백 번 호출될 수 있음). 세션이
    끊기면 `reset()` 후 다음 호출에서 재연결한다. 접속 정보는 생성 시 주입(호출부가 env에서
    읽어 넘김 → 코드/깃에 비밀 없음).

    호스트 키는 `AutoAddPolicy`로 자동 수용한다(내부/테스트 서버 대상, `io/sftp.py`와 동일 정책).
    """

    def __init__(
        self,
        host: str,
        *,
        port: int = 22,
        user: str,
        password: str | None = None,
        pkey_path: str | None = None,
        timeout: int = 10,
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._pkey_path = pkey_path
        self._timeout = timeout
        self._client: paramiko.SSHClient | None = None

    @property
    def timeout(self) -> int:
        return self._timeout

    def _connect(self) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                self._host,
                port=self._port,
                username=self._user,
                password=self._password,
                key_filename=self._pkey_path,
                timeout=self._timeout,
                allow_agent=False,
                look_for_keys=False,
            )
        except paramiko.AuthenticationException as e:
            raise SshError(f"SSH 인증 실패: {self._user}@{self._host}:{self._port} ({e})") from e
        except (paramiko.SSHException, OSError) as e:
            raise SshError(f"SSH 접속 실패: {self._host}:{self._port} ({e})") from e
        return client

    def client(self) -> paramiko.SSHClient:
        """이미 연결돼 있으면 재사용, 없으면 새로 맺는다."""
        if self._client is None:
            self._client = self._connect()
        return self._client

    def reset(self) -> None:
        """세션이 끊겼을 때 정리 — 다음 `client()`에서 재연결하도록 상태를 비운다."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def close(self) -> None:
        """세션을 명시적으로 닫는다(요청 종료 시 팩토리가 호출). 반복 호출해도 안전."""
        self.reset()

    def __enter__(self) -> "SshConnection":
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()


class SshCommandRunner:
    """SSH exec로 원격 명령을 실행하는 얇은 원시. `run(argv)` 하나만 제공한다.

    `argv`는 **문자열이 아니라 토큰 리스트**로 받아 내부에서 `shlex.join`으로 합친다 —
    사용자 입력(테이블명 등)이 인자로 들어와도 셸 인젝션이 구조적으로 막힌다. 원시가
    하나뿐이라 안전 지점도 여기 한 곳으로 모인다.

    유휴 타임아웃 등으로 재사용 세션이 끊겨 있을 수 있어, 연결 오류 시 세션을 버리고
    한 번 재연결해 재시도한다(`io/sftp.py`의 read/listdir와 동일한 2회 시도 패턴).
    """

    def __init__(self, conn: SshConnection, *, encoding: str = "utf-8") -> None:
        self._conn = conn
        self._encoding = encoding

    def run(self, argv: list[str], *, timeout: int | None = None) -> CommandResult:
        if not argv:
            raise SshError("빈 argv로는 명령을 실행할 수 없다")
        command = shlex.join(argv)
        eff_timeout = timeout if timeout is not None else self._conn.timeout

        for attempt in (1, 2):
            client = self._conn.client()
            try:
                _stdin, stdout, stderr = client.exec_command(command, timeout=eff_timeout)
                # stdout를 EOF까지 읽어 명령 종료를 기다린 뒤 exit code를 회수한다.
                # (grep -l 등 출력이 작은 명령 전제. 대용량 출력은 stderr 버퍼 교착
                #  가능성이 있어, 그런 명령이 생기면 채널을 스트리밍으로 소비해야 한다.)
                out_bytes: bytes = stdout.read()
                err_bytes: bytes = stderr.read()
                code = stdout.channel.recv_exit_status()
                break
            except (paramiko.SSHException, EOFError, OSError) as e:
                self._conn.reset()
                if attempt == 2:
                    raise SshError(f"SSH 명령 실패: {command!r} ({e})") from e
                logger.debug("SshCommandRunner run: 세션 끊김, 재연결 후 재시도 %r", command)

        out = out_bytes.decode(self._encoding, "replace")
        err = err_bytes.decode(self._encoding, "replace")
        logger.debug(
            "SshCommandRunner run: %r → exit=%d (out %d chars, err %d chars)",
            command, code, len(out), len(err),
        )
        return CommandResult(stdout=out, stderr=err, exit_code=code)


def grep_files(
    runner: CommandRunner,
    needle: str,
    root: str,
    *,
    word: bool = False,
    ignore_case: bool = True,
) -> list[str]:
    """`root` 아래에서 `needle`을 포함하는 파일 경로 목록을 돌려준다(매칭된 파일명만).

    Impact Analysis 1홉의 **싼 후보 필터**다 — 수천 개 소스를 열지 않고 grep으로 몇 개로
    좁힌 뒤, 정밀 확정(파싱)은 호출부가 한다. 놓침 0이 중요하므로 기본은 **느슨하게**
    잡는다(`word=False`: 부분 문자열도 후보에 포함, 오탐은 후속 파싱이 거름).

    - `-r` 재귀, `-l` 파일명만, `-F` 고정 문자열(정규식 메타문자·`$` 등을 리터럴 취급),
      `-i` 대소문자 무시(Oracle 관행), `word=True`면 `-w`(단어 경계)로 조인다.
    - needle은 argv 토큰으로 넘겨 셸 해석을 거치지 않는다(`-F`와 이중 안전).
    - grep exit code: 0=매칭 있음, 1=매칭 없음(정상 → 빈 목록), 2 이상=실제 오류(SshError).
    """
    flags = "-rlF"
    if ignore_case:
        flags += "i"
    if word:
        flags += "w"

    result = runner.run(["grep", flags, needle, root])
    if result.exit_code == 1:
        return []
    if result.exit_code >= 2:
        raise SshError(f"grep 실패(exit={result.exit_code}): {result.stderr.strip()!r}")
    return [line for line in result.stdout.splitlines() if line]


def default_command_runner() -> Iterator[CommandRunner]:
    """env(NOGADA_SFTP_*)에서 SshCommandRunner 생성. SFTP reader와 같은 서버로 붙는다.

    회사 서버는 하나뿐이라 파일 읽기(default_reader)와 명령 실행이 같은 접속 정보를
    공유한다(그래서 별도 NOGADA_SSH_* 를 두지 않고 NOGADA_SFTP_* 를 재사용). 라우터에
    FastAPI `Depends(default_command_runner)`로 주입하면 테스트에서 fake로 교체 가능.

    yield 의존성이라 요청 하나가 끝날 때까지 세션 하나를 재사용하다가 응답 후 닫는다.

    `NOGADA_SOURCE_ENCODING`(기본 `utf-8`)으로 명령 stdout/stderr 바이트→문자열 디코딩
    인코딩을 지정한다 — `io/sftp.py::default_reader`와 같은 env를 공유한다(같은 서버라
    인코딩도 같다는 전제).
    """
    host = os.environ.get("NOGADA_SFTP_HOST", "127.0.0.1")
    port = int(os.environ.get("NOGADA_SFTP_PORT", "2222"))
    user = os.environ.get("NOGADA_SFTP_USER", "testuser")
    encoding = os.environ.get("NOGADA_SOURCE_ENCODING", "utf-8")
    logger.debug("default_command_runner: SSH runner 생성 %s@%s:%d encoding=%s", user, host, port, encoding)

    conn = SshConnection(
        host,
        port=port,
        user=user,
        password=os.environ.get("NOGADA_SFTP_PASS", "testpass"),
    )
    try:
        yield SshCommandRunner(conn, encoding=encoding)
    finally:
        conn.close()
