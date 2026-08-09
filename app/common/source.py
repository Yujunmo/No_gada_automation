"""원격 소스 접근 추상화 (툴 공용 I/O 인프라).

"경로를 주면 파일 내용을 문자열로 돌려준다"는 한 가지 동작만 제공한다.
`SourceReader` 인터페이스 뒤에 `SftpSourceReader`(실제 접속) 구현을 숨긴다. 개발/검증은
로컬 Docker SFTP(`remote_server/`, 127.0.0.1:2222)로, 단위 테스트는 인메모리 가짜 reader로
이 인터페이스를 만족시킨다. 특정 도구 지식이 없는 범용 인프라라 `app/common/`에 둔다(같은 범주: text.py).
이용하는 도구가 `reader.read(path)`만 호출하므로 SFTP 접속 코드는 이 파일 한 곳에만 존재한다.
"""
from __future__ import annotations

import logging
import os
from typing import Protocol, runtime_checkable

import paramiko

logger = logging.getLogger("no_gada.source")


class SourceNotFound(Exception):
    """요청한 경로의 파일을 소스에서 찾지 못함."""


class SourceError(Exception):
    """소스 접근 자체가 실패(접속/인증/전송 오류 등). 파일 부재(SourceNotFound)와 구분."""


@runtime_checkable
class SourceReader(Protocol):
    """경로 → 파일 내용(str). 없으면 SourceNotFound, 접근 실패면 SourceError."""

    def read(self, path: str) -> str: ...


class SftpSourceReader:
    """SFTP(SSH) 원격 서버를 소스로 쓰는 reader.

    접속 정보는 생성 시 주입한다(호출부가 환경변수에서 읽어 넘김 → 코드/깃에 비밀 없음).
    `read`마다 접속/해제하는 단순 모델(상태 없는 세션). 로컬 Docker SFTP든 회사 서버든
    타는 paramiko 경로는 동일하므로 반입 후에는 접속 정보만 교체하면 된다.

    회사 서버 프로토콜이 SFTP라 FTP(ftplib)가 아니라 SSH 위 SFTP를 쓴다.
    호스트 키는 `AutoAddPolicy`로 자동 수용한다(내부/테스트 서버 대상. atmoz/sftp는
    recreate 시 호스트 키가 바뀌므로 known_hosts 고정이 오히려 마찰을 준다).
    """

    def __init__(
        self,
        host: str,
        *,
        port: int = 22,
        user: str,
        password: str | None = None,
        pkey_path: str | None = None,
        base_dir: str = "",
        encoding: str = "utf-8",
        timeout: int = 10,
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._pkey_path = pkey_path
        self._base = base_dir.rstrip("/")
        self._encoding = encoding
        self._timeout = timeout

    def read(self, path: str) -> str:
        """SFTP 접속 후 remote 경로를 읽어 문자열로 돌려준다."""

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
            raise SourceError(f"SFTP 인증 실패: {self._user}@{self._host}:{self._port} ({e})") from e
        except (paramiko.SSHException, OSError) as e:
            raise SourceError(f"SFTP 접속 실패: {self._host}:{self._port} ({e})") from e

        try:
            sftp = client.open_sftp()
            try:
                with sftp.open(path, "r") as f:
                    data: bytes = f.read()
            except FileNotFoundError as e:
                # 경로 없음 → 부재로 취급 (paramiko는 IOError 계열을 던짐)
                raise SourceNotFound(f"파일 없음: {path} ({e})") from e
            except OSError as e:
                raise SourceError(f"SFTP 전송 실패: {path} ({e})") from e
            finally:
                sftp.close()
        finally:
            client.close()

        text = data.decode(self._encoding, "replace")
        logger.debug("SftpSourceReader read: %s (%d chars)", path, len(text))
        return text


def default_reader() -> SourceReader:
    """env(NOGADA_SFTP_*)에서 SftpSourceReader 생성. 기본값은 로컬 Docker SFTP 테스트 서버.

    회사 SFTP 서버는 하나뿐이라 여러 툴이 이 팩토리를 공유한다. 라우터에 FastAPI
    `Depends(default_reader)`로 주입하면 테스트에서 `app.dependency_overrides`로 교체 가능.
    """
    host = os.environ.get("NOGADA_SFTP_HOST", "127.0.0.1")
    port = int(os.environ.get("NOGADA_SFTP_PORT", "2222"))
    user = os.environ.get("NOGADA_SFTP_USER", "testuser")
    base_dir = os.environ.get("NOGADA_SFTP_BASE", "src")
    logger.debug("default_reader: SFTP reader 생성 %s@%s:%d base_dir=%s", user, host, port, base_dir)

    return SftpSourceReader(
        host,
        port=port,
        user=user,
        password=os.environ.get("NOGADA_SFTP_PASS", "testpass"),
        base_dir=base_dir,
    )
