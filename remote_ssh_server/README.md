# 테스트용 SSH + SFTP 원격 서버

`table_extractor`의 원격 파일 가져오기(SFTP)와 Impact Analysis의 원격 grep(SSH 명령 실행)을
검증하기 위한 **로컬 SSH+SFTP 서버**(Docker). 실제 회사 서버가 SFTP(SSH)고 exec(grep)도
지원하므로 하나의 openssh(alpine) 이미지로 두 경로를 다 리허설한다(하나의 sshd가 exec와
(internal-)sftp를 함께 제공).

## 접속 정보

| 항목 | 값 |
|------|-----|
| host | `127.0.0.1` |
| port | `2222` |
| user | `testuser` |
| password | `testpass` |

앱은 절대경로 `/truap01dap1/...`로 접근한다(`PROFRAME_ROOT="/truap01dap1/proframe/proframe5.0"`).
`truap01dap1/`을 컨테이너의 **실제 `/truap01dap1`**에 얹으므로, SFTP `open("/truap01dap1/...")`과
exec `grep /truap01dap1/...`이 **동일 경로**를 본다.

## 컨텐츠

`truap01dap1/` 아래가 서버에 그대로 노출된다(읽기 전용 마운트 — 조회 도구라 충분). 사내
프로젝트 구조를 껍데기만 흉내 낸 픽스처다: 실제 소스는 없고 대부분 0바이트 파일 + 빈
디렉토리, DBIO XML만 `table_extractor` 검증을 위해 실제 파싱 가능한 내용을 채워뒀다.

```
truap01dap1/proframe/proframe5.0/
├── compile/<PROG>/src/{batch, module, serviceModule}/*.c   # 원본 C 소스
└── release/dbio/xml/pfmDbio<ID>.xml                        # 배포 DBIO SQL 리소스(평면 구조)
```

소스 픽스처를 고치려면 `remote_ssh_server/truap01dap1/`을 직접 편집하면 된다(컨테이너와
실시간 연동, 호스트 ↔ 컨테이너 어느 쪽에서 바꿔도 즉시 반영).

## 사용법

```bash
cd remote_ssh_server
docker compose up -d --build   # 기동 (첫 실행은 이미지 빌드)
docker compose ps              # 상태
docker compose logs -f ssh     # 로그
docker compose down            # 정지
```

> **호스트 키 참고**: 컨테이너를 **recreate**(설정/이미지 변경 후 `up`)하면 SSH 호스트 키가
> 새로 생성돼 클라이언트의 `known_hosts`와 충돌할 수 있다. 이때는 `ssh-keygen -R "[127.0.0.1]:2222"`.
> 단순 `stop`/`start`나 `restart`로는 키가 유지된다.

## 수동 접속 확인

```bash
# SFTP 읽기
sftp -P 2222 testuser@127.0.0.1        # 암호 testpass

# SSH 명령 실행 (grep 후보 필터)
ssh -p 2222 testuser@127.0.0.1 \
  "grep -rlFi TRU_SRVC_BTN_LB /truap01dap1/proframe/proframe5.0/release/dbio/xml"
```

앱 코드(`app/common/io/ssh.py`)로 검증하려면 `SshCommandRunner`/`grep_files`와
`SftpSourceReader`를 `127.0.0.1:2222`로 붙이면 된다.
