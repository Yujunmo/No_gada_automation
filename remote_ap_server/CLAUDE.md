# CLAUDE.md — remote_server/

이 디렉토리는 `table_extractor`의 원격 파일 가져오기를 검증하기 위한 **테스트용 SFTP 서버**다.
실제 회사 서버 프로토콜이 SFTP(SSH)라, 그 접속 경로를 로컬 Docker로 리허설한다.
**기존 노가다 프로그램(`app/` 등)과 독립** — 여기서는 서버 환경만 다룬다.

## 구성

| 파일 | 역할 |
|------|------|
| `docker-compose.yml` | `atmoz/sftp` 컨테이너. 포트 2222, `files/`를 쓰기 가능 마운트 |
| `files/` | 서버에 노출되는 테스트 소스(호스트 ↔ 컨테이너 실시간 연동) |
| `README.md` | 접속 정보·사용법 상세 |

## 접속 정보

| host | port | user | password | base |
|------|------|------|----------|------|
| 127.0.0.1 | 2222 | testuser | testpass | `src` |

- 경로 매핑: 컨테이너 `/home/testuser/src` = 호스트 `files/`. SFTP 접속 후엔 `src/dbio/...`로 보인다.
- **쓰기 가능**: SFTP로 `src/` 안 파일 추가·수정·삭제 OK (호스트 `files/`에 즉시 반영).

## 테스트 소스 트리 (`files/`)

사내 프로젝트 구조를 **껍데기만** 흉내 낸 픽스처다 — 실제 소스는 없고 **0바이트 파일 + 빈 디렉토리**뿐. `table_extractor`가 원격 소스를 스캔할 때의 **경로·네이밍 규칙**을 리허설하는 용도이므로, 파일이 비어 있는 건 정상이다(스캔 검증 시 내용 채움).

루트: `files/` = 컨테이너 `src/` → 그 아래 `truap01dap1/proframe/proframe5.0/`. **두 축**으로 나뉜다.

```
truap01dap1/proframe/proframe5.0/
├── compile/<PROG>/src/{batch, module, serviceModule}/*.c   # 원본 C 소스
│     └ 예: PCSP/src/batch/BPCOMBASC072.c
│           PCSP/src/module/MPCOM_InsFndTmp.c
│           PCSP/src/serviceModule/SPCSP53619A/SPCSP53619A.c
└── publish_ecams/resource/<PROG>/{DYNAMICSQL, EXECSQL, PERSIST, VIEW}/   # 배포 SQL 리소스
      └ 예: PCSP/DYNAMICSQL/PFO_FUND_BS_DF037/PFO_FUND_BS_DF037.xml
```

- **프로그램 코드(`<PROG>`)**: `NCOM NCSP PCOM PCSH PCSP PPFR RLGR` — 두 축 양쪽에 대칭으로 존재.
- 현재 실경로 샘플은 **`PCSP` 라인에만** 있음(.c 3개 + `.xml` 1개, 모두 0바이트). 나머지 프로그램·종류는 빈 디렉토리.
- **주의**: `files/.DS_Store`(macOS 부산물)가 SFTP로도 노출됨 → 스캔 로직에서 필터 대상.

## 자주 쓰는 명령

```bash
docker compose up -d          # 기동
docker compose ps             # 상태
docker compose logs -f sftp   # 로그
docker compose down           # 정지

# 컨테이너 내부 셸 (SSH 아님 — 이 이미지는 SFTP 전용)
docker exec -it remote_server-sftp-1 /bin/sh

# 수동 SFTP
sftp -P 2222 testuser@127.0.0.1
```

## 주의

- `atmoz/sftp`는 **SFTP 전용**이라 `ssh` 대화형 셸 로그인은 막혀 있다. 내부 확인은 `docker exec` 사용.
- 컨테이너 **recreate** 시 SSH 호스트 키가 새로 생성돼 `known_hosts` 충돌 경고가 날 수 있다
  → `ssh-keygen -R "[127.0.0.1]:2222"`. (단순 restart/stop·start는 키 유지)
- 이미지가 `linux/amd64`라 arm64 Mac에서는 에뮬레이션으로 동작(테스트엔 무방).
