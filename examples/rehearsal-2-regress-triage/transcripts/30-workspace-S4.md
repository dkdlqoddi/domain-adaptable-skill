> 입력: `/workspace generate (CONTRACT v2의 F7을 작업판에 슬라이스로 넣어 주세요.)`

F7을 작업판에 **S4**로 넣고 커밋했습니다(`04cc30c`).

| ID | 슬라이스 | SPEC | 쓰기 범위 | 검증 명령 | 상태 |
|---|---|---|---|---|---|
| S4 | (P1, S3 다음) 나눠 올리기: 글이 4000바이트를 넘는 날에만 묶음 줄 경계에서 메시지 N개로 나눈다. 보관 파일은 나누지 않는다 | F7, CONTRACT C "나눠 올리기", D-007 | `regsum.py`, `test_regsum.py` | `python3 -m unittest -q test_regsum && bash fixtures/check.sh` → ①~⑤ PASS | TODO |

세부 기준은 표에 다시 적지 않았습니다. SPEC의 F7 세부 규칙과 CONTRACT C 절을 가리키게 했습니다.

**감사 결과**
- [x] 쓰기 범위가 겹치지 않음: 모듈이 `regsum.py` 하나뿐이고, 슬라이스는 순서대로 진행합니다.
- [x] 가리키는 경로가 모두 있음: `docs/CONTRACT.md`와 ⑤에 필요한 `fixtures/split_logs/2026-10-26/`, `fixtures/history_split/2026-10-25.tsv`, `fixtures/expected/2026-10-26_split.{txt,tsv}`가 이미 있어서 새로 만든 fixture는 없습니다.
- [x] 검증 명령이 실행됨: 단위 테스트는 OK입니다. `check.sh`는 ①②③ PASS, ④ⓐ·ⓑ와 ⑤ FAIL입니다. 아직 구현하지 않아서 실패하는 것이고 명령 자체는 맞습니다.
- [x] CLAUDE.md 길이: 루트가 44줄로 80줄 이하입니다. 모듈이 하나라 모듈별 CLAUDE.md는 만들지 않았습니다.
- [x] S0 있음(DONE)
- [x] 모듈 수 1개(4개 이하)

**참고:** S4 검증 명령은 ④ PASS까지 요구해서 S3가 끝나야 통과합니다. SPEC에도 "P0(S3까지) 다음"이라고 되어 있어 일부러 이렇게 두었습니다.

추가하지 않은 것: 모듈별 CLAUDE.md(모듈이 하나라 필요 없음), 새 fixture(이미 있음), S4를 더 쪼갠 슬라이스(F7 기능 하나라 하나로 충분하다고 봤음).
확인하지 못한 것·리스크: ⑤ 기대 출력 파일이 CONTRACT 규칙과 맞는지(메시지마다 4000바이트 이하인지 등)는 다시 확인하지 않았습니다. 이 파일들은 `/spec` 단계에서 만든 것입니다.

다음: `/delegate S0`(S0는 이미 끝났으니 실제로 이어 갈 작업은 `/delegate S3`, 그다음 `/delegate S4`입니다)
