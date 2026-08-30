# CLAUDE.md — remote_ssh_server/

이 디렉토리는 `data_migration`의 원격 파일 가져오기(SFTP)와 Impact Analysis의 원격
grep(SSH 명령 실행)을 검증하기 위한 **테스트용 SSH+SFTP 서버**다. 실제 회사 서버 프로토콜이
SFTP(SSH)고 exec(grep)도 지원하므로, 그 접속 경로를 로컬 Docker로 리허설한다.
**기존 노가다 프로그램(`app/` 등)과 독립** — 여기서는 서버 환경만 다룬다.

## 구성

| 파일 | 역할 |
|------|------|
| `Dockerfile` | alpine + openssh(exec + internal-sftp) 커스텀 이미지 |
| `docker-compose.yml` | 포트 2222, `truap01dap1/`를 읽기 전용 마운트 |
| `truap01dap1/` | 서버에 노출되는 테스트 소스(호스트 ↔ 컨테이너 실시간 연동, 실 사내 절대경로와 동일한 폴더명) |
| `README.md` | 접속 정보·사용법 상세 |

## 접속 정보

| host | port | user | password |
|------|------|------|----------|
| 127.0.0.1 | 2222 | testuser | testpass |

경로 매핑: 컨테이너 절대경로 `/truap01dap1` = 호스트 `truap01dap1/`(chroot 트릭 없이 그대로
얹음, 실 사내 서버의 절대경로와 동일). 읽기 전용 마운트라 SFTP put/rm은 안 됨(조회 도구라
충분 — 픽스처를 고치려면 호스트 `truap01dap1/`을 직접 편집).

## 테스트 소스 트리 (`truap01dap1/`)

사내 프로젝트 구조를 흉내 낸 픽스처다 — 대부분 **0바이트 placeholder 파일 + 빈 디렉토리**고,
일부만(DBIO XML 25개, 일부 PROG의 serviceModule/batch C 소스) 실제 파싱 가능한 내용을 채워
`data_migration`/`refs.py` 검증에 쓴다. `data_migration`가 원격 소스를 스캔할 때의
**경로·네이밍 규칙**을 리허설하는 용도이므로, 나머지가 비어 있는 건 정상이다.

루트: `truap01dap1/` → `proframe/proframe5.0/`. **두 축**으로 나뉜다.

```
truap01dap1/proframe/proframe5.0/
├── compile/<PROG>/src/{batch, module, serviceModule}/*.c   # 원본 C 소스
│     └ 예: PCSP/src/serviceModule/SPCSP53619C/SPCSP53619C.c
│           RLGR/src/batch/BRLGRPRP0001.c
└── release/dbio/xml/pfmDbio<ID>.xml                        # 배포 DBIO SQL 리소스(완전 평면 구조)
```

- **프로그램 코드(`<PROG>`)**: `NCOM NCSP PCOM PCSH PCSP PPFR RLGR` — `compile/` 축 전체에 대칭으로 존재.
- **주의**: `truap01dap1/.DS_Store`(macOS 부산물)가 SFTP로도 노출됨 → 스캔 로직에서 필터 대상.

## 자주 쓰는 명령

```bash
docker compose up -d --build   # 기동 (첫 실행/Dockerfile 변경 시 --build)
docker compose ps              # 상태
docker compose logs -f ssh     # 로그
docker compose down            # 정지

# 컨테이너 내부 셸 (일반 openssh라 SSH 대화형 로그인도 가능)
docker exec -it remote_ssh_server-ssh-1 /bin/sh

# 수동 SFTP / SSH exec
sftp -P 2222 testuser@127.0.0.1
ssh -p 2222 testuser@127.0.0.1 "grep -rlFi TRU_SRVC_BTN_LB /truap01dap1/proframe/proframe5.0/release/dbio/xml"
```

## 주의

- 컨테이너 **recreate**(설정/이미지 변경 후 `up`) 시 SSH 호스트 키가 새로 생성돼 `known_hosts`
  충돌 경고가 날 수 있다 → `ssh-keygen -R "[127.0.0.1]:2222"`. (단순 restart/stop·start는 키 유지)
