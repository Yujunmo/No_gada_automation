"""원격 소스 접근 추상화 (툴 공용 I/O 인프라).

"경로를 주면 파일 내용을 문자열로 돌려준다"는 한 가지 동작만 제공한다.
`SourceReader` 인터페이스 뒤에 `FtpSourceReader`(실제 접속) 구현을 숨긴다. 개발은
루프백 FTP(127.0.0.1)로, 단위 테스트는 인메모리 가짜 reader로 이 인터페이스를 만족시킨다.
특정 도구 지식이 없는 범용 인프라라 `app/common/`에 둔다(같은 범주: text.py).
이용하는 도구가 `reader.read(path)`만 호출하므로 FTP 접속 코드는 이 파일 한 곳에만 존재한다.
"""
from __future__ import annotations

import ftplib
import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger("no_gada.source")


class SourceNotFound(Exception):
    """요청한 경로의 파일을 소스에서 찾지 못함."""


class SourceError(Exception):
    """소스 접근 자체가 실패(접속/전송 오류 등). 파일 부재(SourceNotFound)와 구분."""


@runtime_checkable
class SourceReader(Protocol):
    """경로 → 파일 내용(str). 없으면 SourceNotFound, 접근 실패면 SourceError."""

    def read(self, path: str) -> str: ...


class FtpSourceReader:
    """FTP 원격 서버를 소스로 쓰는 reader.

    접속 정보는 생성 시 주입한다(호출부가 환경변수에서 읽어 넘김 → 코드/깃에 비밀 없음).
    `read`마다 접속/해제하는 단순 모델(상태 없는 세션). 루프백이든 회사 서버든
    타는 ftplib 경로는 동일하므로 반입 후에는 접속 정보만 교체하면 된다.

    `tls=True`면 FTPS(FTP over TLS). SFTP(SSH)는 프로토콜이 달라 여기서 다루지 않는다.
    """

    def __init__(
        self,
        host: str,
        *,
        port: int = 21,
        user: str = "anonymous",
        password: str = "",
        base_dir: str = "",
        tls: bool = False,
        encoding: str = "utf-8",
        timeout: int = 10,
        passive: bool = True,
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._base = base_dir.rstrip("/")
        self._tls = tls
        self._encoding = encoding
        self._timeout = timeout
        self._passive = passive

    def _full_path(self, path: str) -> str:
        rel = path.lstrip("/")
        return f"{self._base}/{rel}" if self._base else rel

    def read(self, path: str) -> str:
        remote = self._full_path(path)
        ftp: ftplib.FTP = ftplib.FTP_TLS() if self._tls else ftplib.FTP()

        try:
            ftp.connect(self._host, self._port, timeout=self._timeout)
            ftp.login(self._user, self._password)
            if self._tls and isinstance(ftp, ftplib.FTP_TLS):
                ftp.prot_p()  # 데이터 채널도 암호화
            ftp.set_pasv(self._passive)
        except ftplib.all_errors as e:
            raise SourceError(f"FTP 접속 실패: {self._host}:{self._port} ({e})") from e

        try:
            chunks: list[bytes] = []
            try:
                ftp.retrbinary(f"RETR {remote}", chunks.append)
            except ftplib.error_perm as e:
                # 550 등 파일 없음/권한 → 부재로 취급
                raise SourceNotFound(f"파일 없음: {remote} ({e})") from e
            except ftplib.all_errors as e:
                raise SourceError(f"FTP 전송 실패: {remote} ({e})") from e

            text = b"".join(chunks).decode(self._encoding, "replace")
            logger.debug("FtpSourceReader read: %s (%d chars)", remote, len(text))
            return text
        finally:
            try:
                ftp.quit()
            except ftplib.all_errors:
                ftp.close()
