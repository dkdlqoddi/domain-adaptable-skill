# 리허설 산출물 — 모의 과제 "인터뷰 연습 도우미"

하네스의 9개 명령을 모의 과제로 처음부터 끝까지 한 번 돌린 결과입니다. "각 단계에서 어떤 문서와 코드가 나오는가"를 보기 위한 예시이며, 실제 해커톤 제출물이 아닙니다.

- 과제 지시문: `task/README.md` (5줄, 일부러 모호함)
- 페르소나 답변: 2회차까지 가공한 것(`transcripts/03`, `05`에 포함). 실제 환경에서는 우측 채팅의 담당자 에이전트에게서 받습니다.
- 실행 방식: 사람이 없는 헤드리스 `claude -p`로, 결정 지점은 "추천안으로 진행하고 `(가정)` 표시" 지시를 붙였습니다. 실제 당일에는 그 지점마다 사람이 답합니다.
- 진행 범위: 슬라이스 S0(걸어다니는 뼈대)까지만 구현했습니다. 그래서 `docs/RETRO.md`는 "P0 미완, 실제라면 제출 불가"라고 적혀 있습니다. 그 솔직함이 의도된 동작입니다.

## 무엇을 보면 좋은가
| 보고 싶은 것 | 파일 |
|---|---|
| 명령별로 화면에 나온 답 | `transcripts/01-kickoff.md` … `11-wrapup.md` (순서대로) |
| 인터뷰가 지식으로 바뀐 모습 | `docs/domain/*.md`, `docs/GLOSSARY.md` |
| 계약 우선의 결과 | `docs/SPEC.md`(P0 2개, 비목표 13개), `docs/CONTRACT.md`, `fixtures/` |
| 모듈 격리 지침 | `api/CLAUDE.md`, `ui/CLAUDE.md` (각 22줄) |
| 위임 브리프 | `docs/briefs/S0.md` |
| 결정과 거절한 AI 제안 | `docs/DECISIONS.md` (D-001~D-010) |
| 복기 문서 | `docs/RETRO.md` |
| 슬라이스 단위 커밋 이력 | `commit-log.txt` |
| S0 코드 | `api/server.py`(106줄), `api/test_server.py`, `ui/index.html`(24줄) |

`gitignore.txt`는 리허설 저장소의 `.gitignore`입니다(선수 실명이 들어갈 `data/`와 스크린샷 폴더 제외).
