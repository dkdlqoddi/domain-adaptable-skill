# 당일 치트시트 — Codex

## 준비 — 터미널에서

| 단계 | 할 일 |
|---|---|
| 사전 점검 | 저장소에서 `bash scripts/check.sh` → `bash scripts/pack.sh` |
| 환경 확인 | `codex --version`·`python3 --version`·`git --version`, 마감 시각 |
| 반입 | `dist/harness.zip`을 과제 루트에 올리고 아래 설치 블록 실행 |
| 충돌 | 쓰기 전에 중단. `--force`는 지침·스킬 백업 후 교체. 기존 docs는 항상 보존 |
| 로컬 설치 | `bash scripts/install.sh <과제 경로>` (기본 Codex) |
| 시작 | 첫 커밋 후 과제 루트에서 `codex` |

```bash
HARNESS_KIT=$(mktemp -d)
unzip -q harness.zip -d "$HARNESS_KIT" || python3 -m zipfile -e harness.zip "$HARNESS_KIT"
bash "$HARNESS_KIT/scripts/install.sh" "$PWD" && rm harness.zip
```

설치가 성공한 뒤 **새 과제 폴더**에서 첫 커밋을 한다. 기존 저장소라면 먼저 `git status --short`로 기존 작업을 확인한다.
`git add`에는 실제 존재하는 초기 자료만 적는다.

```bash
git rev-parse --git-dir >/dev/null 2>&1 || git init
git config user.email >/dev/null || git config user.email "me@example.com"
git config user.name  >/dev/null || git config user.name "이름"
git add -- README.md AGENTS.md .agents/ docs/    # + 검토한 과제 파일
git diff --cached --stat && git commit -qm "init: 과제와 Codex 하네스"
codex
```

## 진행 — Codex 입력창에서 (4시간 기준)

`$스킬명`은 셸 명령이 아니다. 아래 입력은 Codex 대화 입력창에서 한다.

| 시간·단계 | 입력 | 할 일·결과 |
|---|---|---|
| 시작 | `$kickoff README.md 13:00` | 한국 시각 마감(또는 `3h45m`, 생략 시 6h). 재정의·모르는 것·시간표 |
| 탐색 ~0:40 | `$interview` | 질문을 본인 말로 바꿔 페르소나에게 묻기 |
| 답 정리 반복 | `$interview <답>` | 기록 + 다음 질문. 중요한 미지수가 있으면 추가 회차 |
| 다지기 | 인터뷰 뒤 자동 진행 | 빈틈 질문 → 요약 → 퀴즈. `그만`으로 종료, 제출과 무관 |
| 계약 ~1:20 | `$spec` | P0≤3·비목표·픽스처·검증 명령·쓰기 범위 확정 |
| 뼈대 | `$delegate S0` | 입력 하나가 끝까지 흐르는 구현·검증·커밋 |
| 구현 ~3:10 | `$delegate <다음 ID>` → `/new` | 브리프·위임·검증·정리·커밋. 상태가 docs에 남은 뒤 새 대화. S2 무렵 실제 출력 시연 |
| 마무리 3:10~4:00 | `$wrapup` | 통합 검증·화면·README·정리 → RETRO → 퀴즈 |

## 인터뷰 사다리 — 한 묶음은 한 칸, 질문 3~5개

| 칸 | 물어볼 것 |
|---|---|
| ① 관찰 | 지금 어떻게 하나, 어디서 시간이 가나, 어디에 기록하나 |
| ② 불편 | 가장 불편한 순간, 실수 지점, 아직 해결하지 못한 이유 |
| ③ 데이터·제약 | 실제 샘플 먼저 확인. 형식·규모·동시 사용·예외·금지 |
| ④ 성공 | 무엇이 되면 됐다고 하나, 하나만 된다면 무엇인가 |
| ⑤ 가설 | 핵심 흐름과 이번에 뺄 것을 현업에게 확인 |

기능 목록을 대신 정해 달라고 묻지 않는다. 탐색 마감이 지나면 `+N분`을 보고 판단한다. 계약으로 넘어가려면 `$spec`. 결정은 자동 기록된다.

## 예외·선택 기능

| 상황 | 대응 |
|---|---|
| 병렬 | `$delegate S1 --parallel`: 독립된 쓰기 범위와 의존성일 때만 |
| 새 요구 | `$interview <답>` → `$spec` → `$delegate <새 ID>` |
| 버그 | 최소 재현 → 원인·파일·검증 3줄 → 최소 수정 → 재검증 |
| 기존 변경 | 보존. 기존 staged가 있으면 자동 커밋 보류, 사유·경로 확인 |
| 커밋 | 검토한 파일만. 다른 브리프·캐시·`.harness-backups/` 제외 |
| 위임 도구 없음·위임 불가 | 같은 브리프·검증 규칙으로 루트에서 순차 구현 |
| 마무리 실패 | 고친 뒤 `$wrapup` 재실행 또는 실패를 RETRO에 기록하고 진행 |
| 검증만 / 복습만 | `$wrapup check` / `$interview quiz` |
| 스킬 미인식 | 과제 루트의 `.agents/skills/` 확인 → `/skills` 또는 `$` → 필요하면 재시작 |
| 과잉 설계 | “SPEC에 근거가 없다. 제거하고 단순하게.” 입력 검증·데이터 보호·보안·접근성 유지 |

## 반입 불가 — 최소 AGENTS.md

```text
# 규칙
- 요구사항·계약·결정은 루트에서, 구현은 작은 슬라이스로. 결정은 추천과 이유를 붙여 하나씩 묻기.
- 상태는 docs/SPEC.md·TASKS.md·DECISIONS.md에 기록. 계약·검증 명령을 정하고 구현.
- SPEC 밖 기능·옵션·추상화는 만들지 않기. 입력 검증·데이터 보호·보안·접근성 유지.
- 버그는 재현부터. 수정 전 원인·파일·검증 설명. 끝나면 검증·보드 갱신·파일별 커밋.
- 기존 변경은 보존. 기존 staged가 있으면 자동 커밋 보류. 답은 짧게, 구현 답 끝에 뺀 것·리스크.
```

전체 설치·충돌 처리·Claude 호환 옵션: [README](../README.md).
