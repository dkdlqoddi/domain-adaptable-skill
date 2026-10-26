#!/bin/bash
# CONTRACT.md "샘플 검증 명령" ①~④를 그대로 돌린다. 루트 소유: 계약이 바뀔 때만 함께 고친다.
# 사용: bash fixtures/check.sh   (실패하면 diff를 보이고 종료코드 1)
cd "$(dirname "$0")/.." || exit 2
# python3는 스크립트가 없어도 종료코드 2를 내므로 ④가 거짓 PASS 되지 않게 먼저 막는다
[ -f regsum.py ] || { echo "FAIL regsum.py 없음"; exit 1; }
r=0
ok() { if [ $? -eq 0 ]; then echo "PASS $1"; else echo "FAIL $1"; r=1; fi; }

# ① 두 밤 순서대로 (F1·F2·F3)
h=$(mktemp -d)
python3 regsum.py samples/2026-10-24 "$h" | diff - fixtures/expected/2026-10-24.txt && diff "$h/2026-10-24.tsv" fixtures/history/2026-10-24.tsv \
  && python3 regsum.py samples/2026-10-25 "$h" | diff - fixtures/expected/2026-10-25.txt && diff "$h/2026-10-25.tsv" fixtures/expected/2026-10-25.tsv
ok "① 두 밤 순서대로"

# ② DMA 사례: 같은 테스트·같은 [SCB], 뒤쪽 메시지만 다름 → 새로 생긴 실패
h=$(mktemp -d); cp fixtures/history_dma_case/*.tsv "$h/"
python3 regsum.py samples/2026-10-25 "$h" | diff - fixtures/expected/2026-10-25_dma_case.txt
ok "② DMA 사례"

# ③ seed 증가 → "1개에서 2개로"
h=$(mktemp -d); cp fixtures/history_seed_growth/*.tsv "$h/"
python3 regsum.py samples/2026-10-25 "$h" | diff - fixtures/expected/2026-10-25_seed_growth.txt
ok "③ seed 증가"

# ④ 실패 경로: 종료코드 2, 보관 파일 안 씀
h=$(mktemp -d)
python3 regsum.py samples/2026-10-99 "$h"; [ $? -eq 2 ] && [ -z "$(ls "$h")" ]
ok "④-a 로그 폴더 없음 → 2"
h=$(mktemp -d); cp fixtures/history_broken/*.tsv "$h/"
python3 regsum.py samples/2026-10-25 "$h"; [ $? -eq 2 ] && [ "$(ls "$h")" = "2026-10-24.tsv" ]
ok "④-b 보관 파일 깨짐 → 2, 새 파일 없음"

# ⑤ 4000바이트 넘는 날 → 줄 경계에서 메시지 2개, 보관 파일은 그대로 (F7)
h=$(mktemp -d); cp fixtures/history_split/*.tsv "$h/"
python3 regsum.py fixtures/split_logs/2026-10-26 "$h" | diff - fixtures/expected/2026-10-26_split.txt && diff "$h/2026-10-26.tsv" fixtures/expected/2026-10-26_split.tsv
ok "⑤ 나눠 올리기"

exit $r
