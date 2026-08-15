# 테스트용 SFTP 원격 서버

`table_extractor`의 원격 소스 파일 가져오기를 검증하기 위한 **로컬 SFTP 서버**(Docker).
실제 회사 서버 프로토콜이 SFTP(SSH)라, 그 접속 경로를 그대로 리허설한다.

## 접속 정보

| 항목 | 값 |
|------|-----|
| host | `127.0.0.1` |
| port | `2222` |
| user | `testuser` |
| password | `testpass` |
| base 디렉토리 | `src` (로그인 후 chroot 홈 기준) |

> 후속으로 프로그램 쪽 접속 코드(`SftpSourceReader` 등)가 이 값을 그대로 쓴다.

## 파일 배치

`files/` 아래가 서버에 그대로 노출된다(**읽기·쓰기 가능**). 로그인 후에는 `src/` 하위로 보이며,
SFTP 유저(`testuser`)가 `src/` 안에서 파일을 **추가·수정·삭제**할 수 있다. 컨테이너에서 바꾼 파일은
호스트 `files/`에 즉시 반영되고, 반대로 호스트 `files/`를 편집하면 컨테이너에도 바로 보인다.

```
files/                       →  로그인 후 src/
  dbio/DBIO_A.xml            →  src/dbio/DBIO_A.xml   (TAB_A/TAB_B 참조, #{status} 바인드)
  service/SVC_SAMPLE.xml     →  src/service/SVC_SAMPLE.xml  (하위 DBIO_A 참조)
```

## 사용법

```bash
cd remote_ap_server
docker compose up -d       # 기동
docker compose ps          # 상태 확인
docker compose logs -f sftp   # 로그
docker compose down        # 정지
```

## 수동 접속 확인

```bash
sftp -P 2222 testuser@127.0.0.1     # 비밀번호: testpass  (호스트 키 최초 확인은 yes)
sftp> ls src/dbio                    # DBIO_A.xml 보임
sftp> get src/dbio/DBIO_A.xml        # 다운로드
sftp> put local.xml src/dbio/NEW.xml # 추가/수정 (쓰기 가능)
sftp> rm src/dbio/NEW.xml            # 삭제
sftp> bye
```

> **호스트 키 참고**: 컨테이너를 **recreate**(`docker compose up` 시 설정/이미지 변경)하면 SSH
> 호스트 키가 새로 생성돼 클라이언트의 `known_hosts`와 충돌할 수 있다. 이때는 해당 항목을 지우면 된다:
> `ssh-keygen -R "[127.0.0.1]:2222"`. 단순 `stop`/`start`나 `restart`로는 키가 유지된다.
