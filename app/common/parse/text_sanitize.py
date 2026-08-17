from __future__ import annotations

import unicodedata


def sanitize_text(text: str) -> tuple[str, list[str]]:
    """보이지 않는 서식문자(Cf) 제거 + 유니코드 공백(Zs) 정규화.

    웹/워드/메신저 등에서 복붙할 때 섞여 들어오는, 사람 눈에 안 보이는
    유니코드 문자를 정리한다. SQL 전용이 아닌 범용 텍스트 유틸이다.

    - 카테고리 Cf(제로폭공백·BOM·소프트하이픈·방향마크·워드조이너 등) → 제거
    - 카테고리 Zs(NBSP·전각공백·U+2000~200A 등) → 일반 공백(' ')으로 치환
    - 그 외(정상 문자, 탭/개행 등 Cc 제어문자) → 그대로 유지

    반환: (정제된 텍스트, 제거/치환된 문자의 'U+XXXX' 목록)
    """
    removed: list[str] = []
    out: list[str] = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat == "Cf":
            removed.append(f"U+{ord(ch):04X}")
        elif cat == "Zs" and ch != " ":
            removed.append(f"U+{ord(ch):04X}")
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out), removed
