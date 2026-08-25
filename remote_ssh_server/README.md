# 테스트용 SSH + SFTP 원격 서버

`remote_ap_server`(atmoz/sftp)의 **확장판**. SFTP 파일 읽기에 더해 **SSH 명령 실행(grep 등)**까지
되는 로컬 Docker 서버다. Impact Analysis 1홉이 "테이블을 쓰는 DBIO 후보"를 원격 `grep`으로
좁히는데, atmoz는 SFTP 서브시스템만 열고 셸 exec를 막아 이 경로를 실측할 수 없다. 일반
openssh(alpine)는 하나의 sshd로 exec와 (internal-)sftp를 함께 제공하므로 이 이미지 하나로
두 경로를 다 리허설한다.

## 접속 정보 (remote_ap_server 와 동일)

| 항목 | 값 |
|------|-----|
| host | `127.0.0.1` |
| port | `2222` |
| user | `testuser` |
| password | `testpass` |

앱은 절대경로 `/src/...`로 접근한다(`PROFRAME_ROOT="/src/truap01dap1/proframe/proframe5.0"`).
그래서 `remote_ap_server/files`를 컨테이너의 **실제 `/src`**에 얹으면, SFTP `open("/src/...")`과
exec `grep /src/...`이 **동일 경로**를 본다(atmoz의 chroot 트릭이 필요 없다).

## 컨텐츠

별도 픽스처를 두지 않는다 — `remote_ap_server/files`를 **볼륨으로 공유**한다(복사 아님, 단일
원본 유지, 읽기 전용 마운트). 즉 소스 픽스처를 고칠 때는 `remote_ap_server/files/`만 편집하면
양쪽 서버에 그대로 반영된다.

## 사용법

```bash
cd remote_ssh_server
docker compose up -d --build   # 기동 (첫 실행은 이미지 빌드)
docker compose ps              # 상태
docker compose logs -f ssh     # 로그
docker compose down            # 정지
```

> ⚠️ **remote_ap_server 와 호스트 포트 2222 를 공유한다.** 이 서버가 sftp+ssh 를 모두 제공하는
> 상위집합이므로 둘 중 **하나만** 띄운다. 이 서버를 쓰려면 `cd ../remote_ap_server && docker compose down`으로
> atmoz 를 먼저 내릴 것. 앱 env(`NOGADA_SFTP_*`)는 바꿀 필요 없다(같은 host/port/user/pass).

## 수동 접속 확인

```bash
# SFTP 읽기 (기존 경로)
sftp -P 2222 testuser@127.0.0.1        # 암호 testpass

# SSH 명령 실행 (신규 경로 — grep 후보 필터)
ssh -p 2222 testuser@127.0.0.1 \
  "grep -rlFi TRU_SRVC_BTN_LB /src/truap01dap1/proframe/proframe5.0/release/dbio/xml"
```

앱 코드(`app/common/io/ssh.py`)로 검증하려면 `SshCommandRunner`/`grep_files`와
`SftpSourceReader`를 `127.0.0.1:2222`로 붙이면 된다.
