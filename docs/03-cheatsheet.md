# 당일 치트시트 (표로 보는 사용법)

## 준비 — 터미널에서

| 단계 | 할 일 |
|---|---|
| 미리 (이 PC) | 저장소에서 `scripts/check.sh` → `scripts/pack.sh`. `dist/harness.zip`과 이 치트시트 챙기기 |
| 환경 확인 | `claude --version`(또는 `codex --version`)·`tmux -V`·`python3 --version`·`git --version`, Codex 로그인·마감 시각 |
| 설치·첫 커밋 | `harness.zip`을 과제 루트에 올리고 아래 블록. Codex는 주석대로 두 곳, 구버전 Claude는 설치 줄에 `--tool claude-commands` |
| 충돌 | 기본은 아무것도 쓰지 않고 중단(zip은 남음). `--force`는 지침·스킬을 백업 후 교체. 기존 docs는 항상 보존 |
| 리허설 (이 PC) | `scripts/install.sh <과제 경로>` 뒤 블록의 `git` 줄부터 |
| 시작 | 과제 루트에서 `claude --model fable` 또는 `codex -m gpt-6-astra`(상 등급 루트). Codex는 `/status`로 승인 정책 확인(샌드박스면 커밋·병렬 시작 때 권한 상승 승인 요청) |

```bash
HARNESS_KIT=$(mktemp -d)
unzip -q harness.zip -d "$HARNESS_KIT" || python3 -m zipfile -e harness.zip "$HARNESS_KIT"
bash "$HARNESS_KIT/scripts/install.sh" "$PWD" && rm harness.zip   # Codex: "$PWD" --tool codex
git rev-parse --git-dir >/dev/null 2>&1 || git init
git config user.email >/dev/null || git config user.email "me@example.com"
git config user.name  >/dev/null || git config user.name "이름"
git add -- README.md CLAUDE.md .claude/ docs/    # + 과제 파일. Codex: AGENTS.md .agents/
git diff --cached --stat && git commit -qm "init: 과제와 하네스"
```

`git add`에는 실제 있는 경로만 적는다(하나라도 없으면 실패). 이미 쓰던 저장소면 먼저 `git status --short`로 섞이면 안 되는 작업을 확인한다.

## 진행 — AI 입력창에서 (4시간 예시)

| 시간·단계 | Claude | Codex | 할 일·결과 |
|---|---|---|---|
| 시작 | `/kickoff README.md 13:00` | `$kickoff README.md 13:00` | 마감 시각(또는 남은 시간 `3h45m`, 생략 시 6h). 과제 재정의, 모르는 것, 시간표 |
| 탐색 ~0:40 | `/interview` | `$interview` | 질문을 본인 말로 바꿔 페르소나에게 묻기 |
| 답 정리 반복 | `/interview <답>` | `$interview <답>` | 답을 붙이면 기록 + 다음 질문. 중요한 미지수가 있으면 추가 회차 |
| 다지기 | 자동 진행 | 자동 진행 | 빈틈 질문 → 요약 → 확인 4문항(파일 없음). 깊은 복습은 `/interview quiz` |
| 계약 ~1:20 | `/spec` | `$spec` | P0≤3·비목표·입출력 픽스처·검증 명령·쓰기 범위 확정 → 구현 계획 10줄 확인·의견 반영 |
| 뼈대 | `/delegate S0` | `$delegate S0` | 입력 하나가 끝까지 흐르는 구현·검증·커밋 |
| 구현 ~3:10 | `/delegate <다음 ID>` → `/clear` | `$delegate <다음 ID>` → `/new` | 마일스톤이면 방식 확인 → 브리프·위임(중 등급)·재검증·회귀·정리·커밋. 커밋(또는 보류 사유)이 docs에 남으면 비우고 다음 슬라이스. P0마다 시연·의견 |
| 마무리 3:10~4:00 | `/wrapup` | `$wrapup` | 통합 검증·README·RETRO·전체 내용 정리 → 16문항 |

## 모델 등급 — 상은 루트만

| 등급 | 누가 | Claude | Codex | 지정 |
|---|---|---|---|---|
| 상 | 루트 | `fable` | `gpt-6-astra` | 시작 옵션·`/model` |
| 중 | 구현 작업자 | `opus` | `gpt-6.1-sol` | 실행기 기본(`--tier implement`) |
| 하 | 검증·단순 수정 | `sonnet` | `gpt-6-luna` | `--tier light` |

## 인터뷰 사다리 — 한 묶음은 한 칸, 질문 3~5개

| 칸 | 물어볼 것 |
|---|---|
| ① 관찰 | 지금 어떻게 하나, 어디서 시간이 가나, 어디에 기록하나 |
| ② 불편 | 가장 불편한 순간, 실수 지점, 아직 해결하지 못한 이유 |
| ③ 데이터·제약 | 실제 샘플을 먼저 확인. 형식·규모·동시 사용·예외·금지 |
| ④ 성공 | 무엇이 되면 됐다고 하나, 하나만 된다면 무엇인가 |
| ⑤ 가설 | 핵심 흐름과 이번에 뺄 것을 현업에게 확인 |

기능 목록을 대신 정해 달라고 묻지 않는다. 탐색 마감이 지나면 `+N분`을 보고 계속할지 판단한다. 계약으로 넘어가려면 `/spec`(Codex `$spec`). 결정은 자동 기록된다.

## 예외·선택 기능

| 상황 | 대응 (Codex는 스킬 앞의 `/`를 `$`로) |
|---|---|
| 병렬 | `/delegate S1`(또는 `--parallel`): tmux + 비대화형 작업자(Claude `claude -p --model opus`, Codex `codex exec --yolo -m gpt-6.1-sol`)에 브리프 전문 전달. 독립 작업 기본 2개, 최대 6개 |
| 순차 | `/delegate S1 --serial`. 선행 의존성 미완료·쓰기 파일·검증 자원 충돌 시에도 순차 |
| 검증·단순 수정만 | 실행기 `--tier light`(하 등급 `sonnet`/`gpt-6-luna`) |
| 새 요구 | `/interview <답>` → `/spec` → `/delegate <새 ID>` |
| 버그 | 최소 재현 → 원인·파일·검증 3줄 → 최소 수정 → 재검증 |
| 기존 변경 | 시작 상태와 비교해 보존. 기존 staged가 있으면 자동 스테이징·커밋 보류, 이유·경로 확인 |
| 커밋 | 검토한 개별 파일만. 다른 브리프·캐시·`.harness-backups/` 제외. 범위 밖 파일 임의 복구 금지 |
| tmux·작업자 CLI 없음·실행 불가 | Agent 도구(Codex는 내장 서브에이전트)에 같은 브리프·등급 모델로 위임, 그것도 없으면 루트에서 순차 구현 |
| 샌드박스 승인 요청 | 커밋·병렬 시작의 권한 상승을 승인. 거절하면 커밋 보류, 병렬은 서브에이전트나 순차 |
| 마무리 실패 | 시간이 있으면 고친 뒤 `/wrapup` 재실행. 없으면 '실패를 RETRO에 적고 진행'을 고른다 |
| 검증만 / 복습만 | `/wrapup check` / `/interview quiz` |
| 과잉 설계 | “SPEC에 근거가 없다. 제거하고 단순하게.” 입력 검증·데이터 보호·보안·접근성은 유지 |

부모는 셸 `sleep`으로 주기 조회하지 않고(Claude Code는 30초 이상의 `sleep`을 막는다) 아래 명령으로 보고·실패·차단이 생길 때까지 기다린다(최대 90초, 단계 갱신으로는 깨지 않음, `--id S1`로 범위 지정). 멈췄거나 실패한 작업만 `status --id S1 --tail 40`으로 화면을 본다.

```bash
python3 .claude/skills/delegate/scripts/tmux_codex.py wait --project "$PWD" --timeout 90
```

Codex 설치에서는 `.claude/skills/`를 `.agents/skills/`로 바꾼다.
병렬 세션의 보고를 모두 회수하고 작업자를 멈춘 뒤 루트가 문서·검증·커밋을 처리한다. `REPORTED_COMPLETE`만으로 DONE 처리하지 않는다. [실행·회수 명령](../harness/.claude/skills/delegate/tmux.md)
학습 문서는 `/interview quiz`와 `/wrapup`에서만 만든다. `KNOWLEDGE.md`: 0절 전체 정리 + 필수 개념·알고리즘·실행 추적·복잡도·대안·한계. `QUIZ.md`: 주제·P0별 문항 연결과 문제, `QUIZ-ANSWERS.md`: 풀이·근거·채점.
퀴즈는 4문항씩, 절반 이상 서술·계산·추적, 문항별 0~2점(전체 채점 시 확인 /8, 복습 /24, 마무리 /32)이다. 약점 보충 최대 2문항. 미응답은 미채점이며 학습 기록은 제출을 막지 않는다.

## 마무리 — 전체 내용을 내 말로 설명하기

`/wrapup`(Codex `$wrapup`)은 아래 내용을 `KNOWLEDGE.md` 0절에 근거와 함께 정리하고, `RETRO.md` 9절과 대화에 7문장 이내로 요약한다.

1. **문제와 목표**: 누구의 어떤 불편을 해결하는가. P0·성공 기준·비목표는 무엇인가.
2. **도메인과 제약**: 단위·용어·현장 규칙·실행 환경에서 무엇을 지켜야 하는가.
3. **전체 동작**: 대표 입력이 어떤 경로로 처리·저장·출력되는가. 실패하면 어떻게 되는가.
4. **핵심 처리**: 알고리즘·자료구조가 왜 맞는가. 경계 사례와 복잡도는 무엇인가.
5. **선택과 대안**: 무엇을 왜 선택·거절했고, 어떤 조건이면 바꾸는가.
6. **실행과 검증**: 어떻게 실행하는가. 실제로 통과한 것과 미완료·실패·미확인은 무엇인가.
7. **한계와 다음 행동**: 남은 한계가 사용자에게 어떤 영향을 주고, 다음에 무엇을 확인하는가.

16문항이 일곱 주제와 모든 P0를 다루는지 범위표로 확인한다. 마지막 문항은 전체 흐름을 1분 분량으로 설명하고 새로운 조건에 적용한다.
`그만`이면 중단하고 `4/16문항 · 6/8점 · 미응답 12문항`처럼 부분 진행을 남긴다. 약점은 근거 코드·테스트로 복습한다. 과거 답·점수는 보존하며, 구현이 달라지면 새 회차·개정으로 연결한다.
하네스 자체를 복습하려면 [README 마지막의 사용법 퀴즈·해설](../README.md#이해-점검-퀴즈--하네스-사용법-12문항)을 푼다.

## 반입 불가 — 최소 지침 (Claude: CLAUDE.md / Codex: AGENTS.md)

```text
# 규칙
- 요구사항·계약·결정은 루트에서, 구현은 작은 슬라이스로. 결정은 추천과 이유를 붙여 하나씩 묻기.
- 상태는 docs/SPEC.md·TASKS.md·DECISIONS.md에 기록. 계약·검증 명령을 정하고 구현.
- SPEC 밖 기능·옵션·추상화는 만들지 않기. 입력 검증·데이터 보호·보안·접근성 유지.
- 버그는 재현부터. 수정 전 원인·파일·검증 설명. 끝나면 검증·보드 갱신·파일별 커밋.
- 기존 변경은 보존. 기존 staged가 있으면 자동 커밋 보류. 답은 짧게, 구현 답 끝에 뺀 것·리스크.
```

전체 설치·충돌 처리와 사용법: [README](../README.md).
