# sshd(명령 실행) + SFTP(파일 전송)를 모두 제공하는 테스트 원격 서버.
#
# atmoz/sftp(remote_ap_server)는 SFTP 서브시스템만 열고 셸 exec를 막아 grep(SSH exec)이
# 안 된다. Impact Analysis 1홉이 원격 grep으로 후보 파일을 좁히므로, exec까지 되는 일반
# openssh 서버가 필요하다. alpine + openssh는 하나의 sshd로 exec와 (internal-)sftp를 함께
# 제공하므로 이 이미지 하나로 두 경로를 다 리허설한다.
FROM alpine:3.20

# openssh(서버+internal-sftp 내장), grep(GNU grep — -r/-l/-F/-i/-w 지원)
RUN apk add --no-cache openssh grep

# 호스트 키 생성 + 테스트 유저(회사 서버와 동일한 testuser/testpass)
RUN ssh-keygen -A \
 && adduser -D testuser \
 && echo "testuser:testpass" | chpasswd

# 비밀번호 인증 켜기 + root 로그인 차단 + SFTP 서브시스템을 internal-sftp로 고정.
# 기존 Subsystem/PasswordAuthentication 라인을 지우고 다시 써 중복 정의 오류를 피한다.
# internal-sftp는 sshd 내장이라 별도 sftp-server 바이너리 경로에 의존하지 않아 견고하다.
RUN sed -i -e '/^#\?PasswordAuthentication/d' -e '/^Subsystem/d' /etc/ssh/sshd_config \
 && printf '\nPasswordAuthentication yes\nPermitRootLogin no\nSubsystem sftp internal-sftp\n' >> /etc/ssh/sshd_config

EXPOSE 22

# -D: 포그라운드, -e: 로그를 stderr로(=docker logs로 바로 보임)
CMD ["/usr/sbin/sshd", "-D", "-e"]
