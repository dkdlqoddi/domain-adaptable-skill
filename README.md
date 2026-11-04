# domain-adaptable-skill

Cofa Probe 환경(크래프톤의 AI 실무 역량 평가 플랫폼)에서 열리는 해커톤을 위한 **개인 하네스**입니다. Claude Code 형식을 원본으로 관리하고, 설치기가 구버전 Claude 명령과 Codex 형식도 생성합니다.
어떤 도메인의 과제가 나와도(웹 서비스, 데이터 파이프라인, EDA 툴 자동화, 사내 자동화 플랫폼) 같은 순서로 일할 수 있게 만들었습니다.

## 30초 설명
Cofa Probe는 결과물만 보지 않습니다. 6시간 동안 **AI와 어떻게 일했는지**(어떤 질문을 했나, 어떻게 쪼개 위임했나, 어떻게 검증했나, AI의 과잉 설계를 통제했나, 토큰을 얼마나 썼나)를 20여 개 평가 에이전트가 기록하고 채점합니다.
이 하네스는 그 평가 방식에 맞는 일하는 순서를 **명령 5개**로 만들고, 과정에서 생기는 지식과 결정을 **`docs/` 폴더의 파일**로 남깁니다. 파일이 남으니 세션을 비워도 안전하고, 토큰이 적게 듭니다. 결정 기록은 명령이 알아서 하고, 명령 하나의 답은 15줄 이내로 짧습니다. 인터뷰가 끝나면 `/interview`가 이어서 도메인 지식을 내 말로 다지고, 요약과 확인 4문항으로 내가 설명할 수 있는지 봅니다. 퀴즈는 커밋·푸시를 막지 않습니다.

`/spec`은 구현 계획을 10줄로 보여 주고 의견을 반영한 뒤 확정하고, `/delegate`는 마일스톤마다 구현 방식을 확인합니다. 독립 슬라이스는 tmux의 비대화형 작업자(Claude 설치는 `claude -p --model opus`, Codex 설치는 `codex exec --yolo -m gpt-6.1-sol`)에 브리프 텍스트를 전달해 병렬 구현합니다. tmux·작업자 CLI가 없으면 Agent 도구에 같은 모델을 지정해 위임하고, 그것도 없으면 순차로 구현합니다. 깊은 복습은 `/interview quiz`(12문항), 마무리는 16문항이며, 학습 문서는 이 두 시점에만 써서 구현 중의 시간과 토큰을 아낍니다. 마지막에는 문제 정의·전체 동작·알고리즘·선택 이유·검증·한계를 정리하고, 모든 P0와 학습 주제를 문제·해설·근거에 연결합니다. `main`은 Claude 원본, `codex`는 Codex 원본이며, 어느 쪽에서 설치해도 같은 도구 형식이면 같은 파일이 만들어집니다.

## 모델 등급 — fable·opus·sonnet (Codex는 astra·sol·luna)

판단은 상 등급 루트가, 구현은 중 등급 작업자가, 되풀이되는 검증·단순 수정은 하 등급이 맡아 토큰을 아낍니다. 상 등급은 루트만 씁니다.

| 등급 | 누가 | 하는 일 | Claude | Codex |
|---|---|---|---|---|
| 상 | 루트 세션 | 재정의·인터뷰·계약·브리프·결정·판정·사람 확인 | `fable` | `gpt-6-astra` |
| 중 | 구현 작업자 | 브리프대로 슬라이스 구현·검증·보고 | `opus` (high) | `gpt-6.1-sol` (high) |
| 하 | 경량 작업자 | 검증·회귀 재실행, 파일 1~2개 단순 수정 | `sonnet` (medium) | `gpt-6-luna` (medium) |

루트는 `claude --model fable`로 시작하고 `/model`로 바꿉니다. 작업자는 실행기가 설치 도구에 맞는 CLI를 `--tier`(기본 `implement`, 검증·단순 수정은 `light`)로 실행합니다. 등급표의 원본은 실행기의 `TIERS`이며, 설치 변환은 Markdown의 모델 이름만 바꿉니다.

## 폴더 지도
```
domain-adaptable-skill/
├── README.md                      ← 지금 이 문서
├── docs/                          ← 사람이 읽는 문서 (하네스에는 포함되지 않음)
│   ├── 01-cofa-probe.md           Cofa Probe가 무엇이고 무엇을 평가하는지
│   ├── 02-strategy.md             전체 전략: 원칙, 세션 구조, 타임박스, 토큰, 리스크
│   ├── 03-cheatsheet.md           당일 한 장 치트시트 (인쇄용)
│   └── 04-design-notes.md         왜 이렇게 설계했나 (grill-with-docs, ponytail, 토큰)
├── harness/                       ← 해커톤 당일 프로젝트에 올리는 것 전부
│   ├── CLAUDE.md                  공통 규칙 (역할, docs 규칙, 결정 기록, 짧은 출력, Git 변경 보존)
│   └── .claude/skills/            5개 스킬 = 5개 슬래시 명령
│       ├── kickoff/               시작: 과제 재정의, 모르는 것, 시간 계획 (+ docs/ 템플릿)
│       ├── interview/             페르소나 질문 생성. 답을 붙이면 정리하고 다음 질문까지, 끝나면 다지기·요약·확인 퀴즈 (+ grill.md)
│       ├── spec/                  SPEC·입출력 샘플·슬라이스 확정 (+ 계약 템플릿·예시, 모듈 지침 템플릿)
│       ├── delegate/              위임·검증·정리·커밋 (+ 브리프, 공통 Git 절차)
│       └── wrapup/                한 번에: 통합 검증, 저장소 정리, 실행 README, 복기 문서, 퀴즈
├── examples/
│   ├── rehearsal-interview-coach/   1차 리허설: 웹 과제, S0까지 (문서, 코드, 명령별 출력)
│   ├── rehearsal-2-regress-triage/  2차 리허설: CLI 과제, P0·P1 완료, 계약 변경·병렬 위임 시험
│   └── rehearsal-3-yield-kit/       직접 하는 리허설용 키트: 처음 보는 반도체 과제 (숨은 사실·정답은 따로)
├── scripts/
│   ├── install.sh                 설치 진입점 (충돌 검사, --tool, --force)
│   ├── install.py                 설치·백업, 구버전 Claude·Codex 변환 (표준 라이브러리)
│   ├── pack.sh                    설치기가 포함된 dist/harness.zip 생성
│   ├── check.sh                   줄 수·프런트매터·참조·추가 토큰 추정·설치 회귀 검증
│   └── test_*.py                  설치·보존·호환·ZIP·tmux 텍스트 전달 검증
└── Cofa Probe 해커톤 준비 전략 분석.txt   원본 분석 대화 (Gemini)
```

Claude용으로 설치하면 과제 프로젝트는 이렇게 됩니다. Codex는 `CLAUDE.md` 대신 `AGENTS.md`, `.claude/skills/` 대신 `.agents/skills/`를 씁니다.
```
<과제 프로젝트>/
├── CLAUDE.md                  규칙 (항상 로드)
├── .claude/skills/…           5개 명령
├── docs/
│   ├── SPEC.md                무엇을 만들고(P0/P1/P2), 무엇을 안 만드나(비목표), 제약, 입출력 샘플(계약)
│   ├── TASKS.md               시간표, 슬라이스 상태, 검증 명령, BLOCKER, 통합 체크포인트
│   ├── DECISIONS.md           결정과 거절한 AI 제안 (D-001, D-002, … 명령이 자동으로 기록)
│   ├── GLOSSARY.md            현업 용어집
│   ├── KNOWLEDGE.md           전체 정리·필수 지식·알고리즘·실행 예·대안
│   ├── QUIZ.md                복습 12문항·마무리 16문항·주제 연결·복습 위치
│   ├── QUIZ-ANSWERS.md        별도 풀이·근거·채점 기준
│   ├── domain/                현업 지식: persona · workflow · constraints · success + 인덱스 (+ 반도체 primer)
│   ├── CONTRACT.md            모듈이 2개 이상일 때만: 모듈 사이 인터페이스 (/spec이 생성)
│   ├── briefs/                위임 브리프 사본 (/delegate가 생성)
│   └── RETRO.md               복기 문서 (/wrapup이 생성)
├── fixtures/                  입출력 샘플 파일 (/spec이 생성)
└── <모듈>/CLAUDE.md           모듈이 2개 이상일 때만, 40줄 이하 지침 (/spec이 생성)
```

## 준비와 설치 (터미널)

설치는 **Bash와 Python 3.8 이상**이 필요합니다(`unzip`이 없으면 Python으로 풉니다). 패키징은 `zip`, 작업에는 Git과 선택한 AI CLI가 필요합니다. 병렬 작업은 루트 CLI와 관계없이 `tmux`와 로그인된 Codex CLI를 사용합니다.

| 순서 | 어디서 | 실행·확인 | 완료 기준 |
|---|---|---|---|
| 1. 사전 점검 | 이 저장소 루트 | `scripts/check.sh` | 정적 검사와 설치 회귀 테스트 통과 |
| 2. 반입 준비 | 이 저장소 루트 | `scripts/pack.sh` | `dist/harness.zip` 생성, 치트시트 준비 |
| 3. 환경 확인 | 과제 터미널 | `claude --version` 또는 `codex --version`, `python3 --version`, `git --version` | 도구·마감 시각·반입·제출 방식 확인 |
| 4. 설치·첫 커밋 | 과제 프로젝트 루트 | `harness.zip`을 올리고 아래 블록 실행 | 설치 완료, `harness.zip` 삭제, 첫 커밋 존재 |
| 5. AI 시작 | 과제 프로젝트 루트 | `claude` 또는 `codex` | 아래 작업 표의 kickoff 실행 |

ZIP은 **설치 키트**입니다. 프로젝트에 직접 덮어 풀지 않고 임시 폴더에 풉니다. 이전 ZIP과 내부 구조가 달라졌으므로 새로 패키징하세요.

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

- git 사용자 설정이 없는 새 폴더에서 이 블록을 그대로 실행해 첫 커밋까지 확인했습니다. 이미 Git 저장소면 `git init`을, 사용자 설정이 있으면 `git config`를 건너뜁니다.
- `git add`에는 실제 있는 경로만 적습니다. 하나라도 없으면 아무것도 추가되지 않습니다. 이미 쓰던 저장소라면 먼저 `git status --short`로 섞이면 안 되는 작업이 없는지 봅니다.
- 설치 줄의 `"$PWD"` 뒤에 `--tool codex` 또는 `--tool claude-commands`를 붙일 수 있습니다. 충돌로 멈추면 `harness.zip`은 남으니 아래 표대로 처리하고 설치 줄부터 다시 실행합니다.
- 리허설처럼 이 PC의 과제 폴더라면 ZIP 없이 `scripts/install.sh /path/to/task`로 설치하고 블록의 `git` 줄부터 실행합니다.

| 사용할 도구 | 설치 옵션 | 설치되는 지침·스킬 | 호출 / 컨텍스트 비우기 |
|---|---|---|---|
| Claude Code | `--tool claude` (생략 가능) | `CLAUDE.md`, `.claude/skills/` | `/kickoff` / `/clear` |
| 스킬을 인식하지 못하는 구버전 Claude | `--tool claude-commands` | 위 파일 + 보조 파일 경로를 보정한 `.claude/commands/*.md` | `/kickoff` / `/clear` |
| Codex | `--tool codex` | `AGENTS.md`, `.agents/skills/`, 스킬별 `agents/openai.yaml` | `$kickoff` / `/new` |

Codex 설치기는 명령 표기·템플릿 경로·모듈 지침 이름을 변환하고 사용자 호출 전용 정책을 생성합니다. 이 정책은 [OpenAI 공식 스킬 문서](https://learn.chatgpt.com/docs/build-skills), `/new`는 [공식 CLI 문서](https://learn.chatgpt.com/docs/developer-commands?surface=cli)에 따릅니다. Codex 설치의 실행기는 `codex exec --yolo -m gpt-6.1-sol` 작업자를 쓰며, 변환은 Markdown의 모델 이름(`fable`·`opus`·`sonnet` → `gpt-6-astra`·`gpt-6.1-sol`·`gpt-6-luna`)도 바꿉니다. tmux·작업자 CLI가 없거나 실행이 허용되지 않으면 같은 브리프를 서브에이전트 도구(Claude는 Agent 도구)에 같은 등급 모델로 넘기고, 그것도 없으면 순차 구현합니다. Codex를 샌드박스 모드(read-only·workspace-write)로 쓰면 `.git`이 읽기 전용이고 tmux 소켓도 막혀, 커밋과 병렬 시작 때 권한 상승 승인을 요청받습니다(`/status`·`/permissions`). 변환·경로는 자동 테스트하며, 각 CLI 버전의 전체 대화형 흐름은 별도 리허설이 필요합니다.

| 설치 상황 | 기본 동작 | 사용자가 할 일 |
|---|---|---|
| 새 프로젝트 / 같은 버전 재설치 | 없는 파일만 생성 / 동일 파일은 건너뜀 | 그대로 사용. 중첩 `skills/skills/`를 만들지 않음 |
| 기존 `CLAUDE.md`만 있음 | 기존 루트 지침 보존, 하네스는 `.claude/CLAUDE.md`에 설치 | 두 지침의 의미 충돌 확인 |
| 두 Claude 지침 모두 다른 내용 / 기존 `AGENTS.md`·스킬이 다름 | **쓰기 전에 중단**, 충돌 경로 출력, 종료코드 2 | 기존 내용과 배포본 비교·병합. 교체를 원하면 같은 명령에 `--force` |
| `--force`로 갱신 | 바뀔 지침·스킬을 `.harness-backups/<시각-고유값>/`에 백업 후 교체 | 기존 사용자 규칙이 필요하면 백업에서 병합. 백업은 커밋에서 제외 |
| 기존 `docs/` 작업 상태 | **`--force`여도 보존**, 없는 템플릿만 추가 | 기존 문서 형식이 다르면 필요한 절만 병합 |

## 전체 사용 순서 (AI 입력창)

명령은 터미널 셸이 아니라 **Claude/Codex 대화 입력창**에 입력합니다. 아래 시간은 4시간 기준입니다. `/kickoff`에 **마감 시각**(한국 시각)을 주면 설치에 쓴 시간을 뺀 남은 시간으로 시간표를 짭니다. `3h45m`처럼 남은 시간을 줘도 되고, 생략하면 6시간입니다.

| 순서·시간 | Claude 입력 | Codex 입력 | 사람이 할 일 | 결과·다음 단계 |
|---|---|---|---|---|
| 1. 시작 | `/kickoff README.md 13:00` | `$kickoff README.md 13:00` | 지시문 경로와 마감 시각(예: 13:00) 전달 | SPEC 초안, 열린 질문, TASKS 시간표 |
| 2. 탐색, ~0:40 | `/interview` | `$interview` | 나온 질문을 본인 말로 바꿔 페르소나에게 묻기 | 질문 3~5개 |
| 3. 답 정리, 반복 | `/interview <답변>` | `$interview <답변>` | 페르소나 답변을 붙여 넣기 | domain·GLOSSARY·SPEC 갱신 + 다음 질문 |
| 4. 다지기·확인 | 인터뷰 종료 뒤 자동 진행 | 동일 | 빈틈 질문에 답하고 확인 4문항. `그만`이면 종료 | 요약·채점(파일 없음). 깊은 복습은 `/interview quiz` |
| 5. 계약, ~1:20 | `/spec` | `$spec` | 필요한 선택을 결정하고 구현 계획 10줄에 의견 주기 | P0≤3, 비목표, 입출력 픽스처, 검증 명령·쓰기 범위가 있는 슬라이스, 반영된 계획 |
| 6. 뼈대 | `/delegate S0` | `$delegate S0` | 제거 후보·화면 확인 요청이 있으면 답하기 | 입력부터 출력까지 동작하는 뼈대, 검증, 커밋 |
| 7. 구현, ~3:10 | `/delegate S1` → `/clear` → 다음 TODO | `$delegate S1` → `/new` → 다음 TODO | 마일스톤(S0·P0 첫 슬라이스·대안 있는 알고리즘)이면 방식에 답하기. 독립 작업은 중 등급 작업자로 자동 병렬. 모든 보고와 커밋(또는 보류 사유) 확인 후 새 세션. P0가 끝나면 시연·의견 | 브리프 → `방식:` 확인 → tmux 구현 → 루트 재검증·정리 → 슬라이스별 커밋 |
| 8. 마무리, 3:10~4:00 | `/wrapup` | `$wrapup` | 화면 확인·정리 후보에 답하고 RETRO·KNOWLEDGE 읽기 | 통합 검증, README, RETRO, 전체 정리, 16문항 퀴즈 |

모든 스킬은 **사람이 호출**합니다. Claude는 `disable-model-invocation: true`, Codex는 `allow_implicit_invocation: false`로 설정합니다. 절차는 5개이며 결정 기록은 명령 안에서 자동으로 남깁니다. 순차 슬라이스는 같은 파일을 확장할 수 있고, 병렬 실행할 때만 범위를 분리합니다.

## 선택 기능과 문제 해결

| 상황 | Claude 입력·행동 | Codex 입력·행동 | 처리 |
|---|---|---|---|
| 독립된 작업을 병렬로 | `/delegate S1` 또는 `--parallel` | `$delegate S1` 또는 `--parallel` | 선행 의존성이 DONE이고 쓰기 파일·검증 자원이 겹치지 않는 TODO를 기본 2개, 최대 6개 병렬 |
| 한 슬라이스만 순차로 | `/delegate S1 --serial` | `$delegate S1 --serial` | 같은 브리프·검증 규칙으로 루트에서 구현 |
| 검증·단순 수정만 위임 | 실행기 `--tier light` | 동일 | 하 등급(`sonnet`/`gpt-6-luna`). 루트에서 1분 안에 끝나면 직접 |
| tmux·작업자 CLI를 못 씀 | 자동으로 Agent 도구(`opus`/`sonnet`)에 위임 | 자동으로 내장 서브에이전트에 위임 | 같은 브리프·등급 모델·회수 규칙. 도구가 없으면 루트에서 순차 구현 |
| 샌드박스가 커밋·실행기를 막음 | 권한 요청에 답하기 | 권한 상승 승인(`/permissions`) | 거절하면 커밋은 보류, 병렬은 서브에이전트나 순차 구현 |
| 구현 중 새 요구 | `/interview <답>` → `/spec` → `/delegate <새 ID>` | `$interview <답>` → `$spec` → `$delegate <새 ID>` | 기존 DONE은 유지, 계약·픽스처 갱신 후 새 슬라이스 추가 |
| 계약 변경 BLOCKER | 루트에서 SPEC·CONTRACT·픽스처 수정 후 재위임 | 동일 | 하위 에이전트가 계약을 임의 변경하지 않음 |
| 검증 실패 | 재현 → 원인·수정 파일·검증 방법 확인 → 수정·재검증 | 동일 | 통과 전 DONE·다음 슬라이스 안내 금지 |
| 기존 staged 변경 | 표시된 경로를 확인해 기존 작업을 별도로 처리 | 동일 | 구현·검증은 가능, 자동 스테이징·커밋은 보류. 기존 변경을 되돌리지 않음 |
| 새 범위 밖 변경 | 경로·출처를 확인 | 동일 | 기존 작업을 보존하며 임의 삭제·복구하지 않음 |
| 마무리 검증만 | `/wrapup check` | `$wrapup check` | 검증·화면·README·정리까지만 |
| 마무리 검증 실패 | 시간이 있으면 고친 뒤 `/wrapup` 재실행 | 고친 뒤 `$wrapup` 재실행 | `/wrapup`이 고칠지, 실패를 RETRO 4절에 적고 진행할지 묻는다. 마감이 가까우면 진행 |
| 복기·퀴즈만 요청 | `/wrapup retro` | `$wrapup retro` | 단독 호출도 통합 검증을 먼저 재실행. 실패가 남으면 위와 같이 묻는다 |
| 복습만 | `/interview quiz` | `$interview quiz` | 학습 문서 작성·갱신 + 12문항 심화 퀴즈. SPEC·TASKS·제출 상태는 유지 |

커밋은 검토한 **개별 파일 경로**만 추가합니다. 기존 staged 변경, 다른 슬라이스의 브리프, 테스트 캐시, 설치 백업을 섞지 않습니다. 공통 절차는 [git-workflow.md](harness/.claude/skills/delegate/git-workflow.md)에 있습니다.

[tmux 실행 절차](harness/.claude/skills/delegate/tmux.md)의 실행기가 브리프와 지침 전문을 초기 프롬프트로 전달합니다. 실행기는 설치된 스킬 폴더로 작업자 CLI를 고르고(Claude: `claude -p --model opus --effort high`, Codex: `codex exec --yolo -m gpt-6.1-sol`), 작업자가 스스로 읽지 않는 쪽의 루트 지침만 자동으로 넣습니다. 모듈 지침만 `--instruction`으로 넘깁니다. `bypassPermissions`와 `--yolo`는 승인과 샌드박스를 끄므로 허용된 작업 환경에서 사용합니다. [공식 CLI 옵션](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
실행기는 같은 프로젝트의 세션을 최대 6개로 제한합니다. 기본 위임은 2개이며, 독립 범위가 확인되면 6개까지 늘립니다. 작업자는 보고를 마치면 스스로 끝나며, 보고 없이 끝나 원인 확인용으로 남은 세션은 종료 전까지 한도에 포함됩니다. 비대화형 실행이라 처음 보는 폴더의 신뢰 확인 화면에서도 멈추지 않습니다.
부모 에이전트(루트)는 셸 `sleep`으로 주기 조회하지 않습니다(Claude Code는 30초 이상의 포그라운드 `sleep`을 막습니다). 결과나 문제가 생길 때까지 기다리는 명령을 씁니다.

```bash
python3 .claude/skills/delegate/scripts/tmux_codex.py wait --project "$PWD" --timeout 90
```

`wait`는 보고 도착·실패·보고 없는 종료·`blocked` 진입이 있거나, 실행 중인 작업이 없거나, 90초가 지나면 `changed`·`running`·`timed_out`과 작업별 상태를 JSON으로 돌려줍니다. 단계·메시지 갱신으로는 깨지 않으므로 작업자가 많아도 부모가 자주 깨지 않고, 진행 상황은 시간 초과 때 한꺼번에 봅니다. 터미널 출력은 싣지 않아 루트 컨텍스트가 덜 쌓입니다. 오래 멈췄거나 실패한 작업만 `status --id S1 --tail 40`으로 화면을 봅니다. 보고 없이 끝난 작업은 원인 확인용으로 화면이 10분 남습니다.
작업자는 단계 전환과 긴 작업의 도구 호출 사이에 전용 `progress.json`을 갱신하고, 질문이 필요하면 입력을 기다리지 않고 BLOCKED로 보고합니다. 갱신 시각은 마지막 보고 시점이며 생존 신호가 아닙니다.
작업자는 겹치지 않는 코드와 전용 진행·보고 파일을 쓰고, 루트는 모든 보고를 회수해 세션을 멈춘 뒤 공유 문서·통합 검증·커밋을 처리합니다. `REPORTED_COMPLETE`는 작업자 보고 도착이며, 루트 검증 후 DONE으로 판정합니다. `FAILED`는 CLI 비정상 종료, `STOPPED`는 보고 없는 종료를 나타냅니다.
Codex 형식으로 설치했다면 위 명령의 `.claude/skills/`를 `.agents/skills/`로 바꿉니다.

## 세 가지 설계 원칙
### 1. 도메인 지식을 쌓는 구조 (grill-with-docs 방식)
grill-with-docs는 계획을 집요하게 인터뷰하면서 합의된 용어를 `GLOSSARY.md`에, 결정을 ADR에 바로 적는 스킬입니다. 여기서는 인터뷰 상대가 사용자가 아니라 **페르소나 에이전트**이므로, `/interview`가 질문을 만들고, 답을 붙여 실행하면 소화해서 `docs/domain/<주제>.md`, `GLOSSARY.md`, `SPEC.md`에 나눠 적은 뒤 다음 질문을 냅니다. `domain/README.md` 인덱스만 읽어도 무엇을 아는지 보이고, 모듈은 필요한 파일 하나만 엽니다. 결정은 명령이 생길 때마다 `DECISIONS.md` 한 파일에 D-NNN으로 쌓습니다.

인터뷰가 끝나면 문서의 빈틈을 한 번에 하나씩 묻고 답을 기존 도메인 문서에 적은 뒤, 요약과 확인 4문항(파일 없음)으로 마칩니다. `/interview quiz`와 `/wrapup`에서만 [학습 문서·출제 기준](harness/.claude/skills/interview/learning.md)에 따라 `KNOWLEDGE.md`에 필수 개념·실제 알고리즘·자료구조·불변식·실행 추적·시간/공간 복잡도·반례·대안·검증 근거를 작성합니다. 설계와 실제 구현을 구분합니다.

`QUIZ.md`는 복습 12문항·마무리 16문항, `QUIZ-ANSWERS.md`는 별도 풀이·근거·채점 기준입니다. 절반 이상은 서술·계산·추적이고 객관식도 이유를 받습니다. 4문항씩 풀고 문항별 0~2점(전체 채점 시 확인 /8, 복습 /24, 마무리 /32)으로 채점하며 약점 보충은 최대 2문항입니다. `그만`이면 남은 학습은 문서에 남깁니다. 학습 기록은 커밋·머지·푸시·제출을 막지 않습니다.

마무리의 `KNOWLEDGE.md` 0절은 **문제와 목표 / 도메인과 제약 / 전체 동작 / 핵심 처리 / 선택과 대안 / 실행과 검증 / 한계와 다음 행동**을 근거와 함께 정리합니다. `RETRO.md` 9절과 대화에는 이를 7문장 이내로 요약합니다. `QUIZ.md`의 범위표로 일곱 주제와 모든 P0가 문항에 연결됐는지 확인하며, 마지막 문항은 전체 흐름을 자기 말로 설명하고 달라진 조건에 적용하는 문제입니다.

답하지 않은 문항은 미채점입니다. 예를 들어 16문항 중 4개를 풀어 6점을 받았다면 `4/16문항 · 6/8점 · 미응답 12문항`으로 기록합니다. 주제별로 설명 확인·보충 필요·미응답을 구분하고 다음 복습 행동을 남깁니다. 구현이 바뀌어도 이미 푼 회차의 답·점수는 보존하며, 현재 문제·해설은 새 회차·개정으로 연결합니다.

### 2. 과잉 설계 방어 (ponytail 방식)
ponytail은 "게으른 시니어 개발자" 규칙입니다. 쓰기 전에 사다리(필요한가 → 이미 있나 → 표준 라이브러리 → 설치된 의존성 → 한 줄 → 최소 구현)를 내려가고, 보안·입력 검증·데이터 보호는 절대 자르지 않으며, 답변 끝에 뺀 것과 리스크를 적습니다. 이 규칙을 `CLAUDE.md`에 12줄로 **항상 켜 두고**(스킬은 모델이 자동으로 꺼내 쓰지 않는 경우가 많아서), 감사는 `/delegate`(슬라이스마다 diff)와 `/wrapup`(제출 전 저장소 전체)이 합니다. Cofa Probe에 맞춰 **쳐낸 것을 `DECISIONS.md`에 자동으로 기록**합니다. 그 기록이 인지 점수와 Q&A 답변의 근거가 됩니다.

### 3. 토큰을 아끼는 구조
| 무엇 | 언제 로드되나 | 크기 (근사) |
|---|---|---|
| 루트 `CLAUDE.md` | 항상 | 80줄 이하, 현재 추정치는 `scripts/check.sh` |
| 스킬 설명 5개 | 항상이지만 사용자 호출 전용이라 | 0 |
| 스킬 본문 1개 | `/명령` 입력 때만 | 120줄 이하 |
| 참고 파일 (Git 절차·브리프·계약·다지기) | 본문이 가리킬 때만 | 파일마다 80줄 이하 |
| 모듈 `CLAUDE.md` | 모듈이 여럿일 때, 그 폴더를 만질 때만 | 40줄 이하 |

이 표는 **하네스가 추가하는 양**이며 시스템 프롬프트·도구·대화·기존 프로젝트 지침을 포함한 전체 세션 비용이 아닙니다. `scripts/check.sh`는 줄 수 한도를 검사하고 바이트 수로 토큰을 추정합니다(실제 토크나이저 측정·토큰 상한 검사는 아님). 슬라이스 완료 후 Claude는 `/clear`, Codex는 `/new`로 비우고 `docs/`에서 재개합니다.

설치 테스트는 학습 문서 보존·실행기 복사·호환 링크·ZIP 동등성을 검사합니다. tmux가 있으면 가짜 Codex·Claude CLI로 텍스트 전달·등급별 모델 선택·6개 동시 실행과 초과 차단·부모의 `wait`·`status` 조회·실패 화면 보존·루트 지침 중복 방지·보고와 실패 구분도 검사합니다. 실행 캐시(`__pycache__`)가 설치·ZIP에 섞이지 않는지도 확인합니다. 실제 모델의 구현 품질과 퀴즈 진행은 별도 리허설 대상입니다.

## 미리 연습하기
- 모의 과제 두 개를 처음부터 끝까지 돌려 봤습니다(명령이 9개였던 이전 버전). 각 단계에서 어떤 문서와 코드가 나오는지 `examples/`에서 훑어볼 수 있습니다.
  - 1차 "인터뷰 연습 도우미"(웹): S0까지 진행
  - 2차 "회귀 결과 정리 도우미"(CLI): P0·P1 완료, 60분
- 3차는 사람이 직접 했고, 18분 만에 "너무 복잡하다"는 결론이 나와 명령을 5개로 줄였습니다. 줄인 하네스로 같은 키트를 다시 해 보세요. 키트는 `examples/rehearsal-3-yield-kit/`에 있고, 방법은 그 폴더의 `README.md`에 있습니다. `persona.md`와 `after-rehearsal/`은 끝날 때까지 열지 마세요.
- 반도체 현장 사전 지식 `harness/.claude/skills/kickoff/templates/docs/domain/primer.md`가 들어 있습니다(SK하이닉스 본선 대비). 설치와 패키징에 자동으로 포함되고, `/interview`가 질문 재료로만 읽습니다. 다른 도메인 대회라면 지우거나 바꾸세요.
- `scripts/check.sh`로 하네스 상태를 확인하고 `scripts/pack.sh`로 zip을 만듭니다.

## 자주 묻는 질문
**웹 프로젝트가 아니어도 되나요?** 됩니다. 하네스 어디에도 frontend/backend 가정이 없습니다. 계약은 API·CLI·파일 포맷·함수·상태 전이 중 맞는 것으로 적습니다. 예시는 `harness/.claude/skills/spec/contract-examples.md`에 있습니다.

**하네스를 못 올리면?** 치트시트 맨 아래의 6줄짜리 최소 CLAUDE.md를 손으로 입력하고 `docs/` 파일 3개(SPEC·TASKS·DECISIONS) 이름만 지키면 같은 흐름으로 일할 수 있습니다.

**명령이 안 보이면?** 설치기에 `--tool claude-commands`를 붙여 다시 실행하고 Claude를 재시작하세요. 보조 파일과 템플릿 경로까지 보정하므로 SKILL.md만 수동 복사하지 않습니다.

**Claude Code 대신 Codex만 있으면?** 설치기에 `--tool codex`를 붙이고 `codex`를 시작하세요. `$kickoff README.md <마감 시각>`부터 위 표대로 진행합니다. 기존 `AGENTS.md`는 자동 덮어쓰지 않습니다. tmux와 Codex가 있으면 병렬 실행하고, 실행할 수 없으면 내장 서브에이전트로, 그것도 없으면 순차 구현합니다. 샌드박스에서는 커밋·병렬 시작 때 권한 상승 승인을 요청받습니다.

**왜 모듈을 많이 안 나누나요?** 나누는 것 자체가 과잉 설계일 수 있습니다. 기본은 1개이고, 검증 방법이 다르거나 병렬로 만들 가치가 있을 때만 나눕니다. 모듈이 1개면 계약(입출력 샘플)은 `SPEC.md` 8절에 두고 `CONTRACT.md`와 모듈 지침은 만들지 않습니다.

**git에 올려도 되나요?** `harness/`는 그대로 커밋해도 됩니다. `dist/`는 `.gitignore`에 있습니다.

## 더 읽기
- [docs/01-cofa-probe.md](docs/01-cofa-probe.md) — 평가 방식과 당일 확인 목록
- [docs/02-strategy.md](docs/02-strategy.md) — 전략 전체
- [docs/03-cheatsheet.md](docs/03-cheatsheet.md) — 한 장 요약
- [docs/04-design-notes.md](docs/04-design-notes.md) — 설계 이유와 확장법

## 전체 내용 정리

이 하네스의 목표는 사용자가 **무엇을 왜 만들었으며, 실제로 어디까지 동작하는지** 근거를 들어 설명하도록 돕는 것입니다.

| 주제 | 기억할 내용 | 다시 볼 곳 |
|---|---|---|
| 저장소와 설치 | 이 저장소는 배포 원본이다. 과제 폴더에 설치하며, 충돌은 쓰기 전에 중단한다. `--force`는 백업 후 지침·스킬을 교체하고 기존 docs는 보존한다 | [설치기](scripts/install.py) |
| 문제 정의 | kickoff에서 모르는 것을 찾고, interview에서 관찰·불편·데이터·성공·가설 순서로 확인한다. 사실·가정·미확인을 구분한다 | [인터뷰](harness/.claude/skills/interview/SKILL.md) |
| 계약과 작업 분할 | P0는 최대 3개, 모듈은 기본 1개다. 비목표·구체적 입출력·실패 예·픽스처·검증 명령을 먼저 정하고 S0부터 만든다 | [계약](harness/.claude/skills/spec/SKILL.md) |
| 구현과 통합 | 독립 작업은 기본 2개, 최대 6개 병렬로 실행한다. 파일뿐 아니라 포트·DB·생성물도 분리한다. 부모는 `wait`로 보고·실패·차단을 기다리고, 보고를 회수해 작업자를 멈춘 뒤 루트가 검증한다. 구현 계획과 마일스톤 방식은 사람이 확인하고, 루트는 상 등급·작업자는 중·하 등급을 쓴다 | [위임](harness/.claude/skills/delegate/SKILL.md) |
| 기록과 변경 보존 | 상태·지식·결정은 docs에 남긴다. 기존 변경을 보존하고 검토한 파일만 커밋한다. 기존 staged 변경이 있으면 자동 커밋을 보류한다 | [Git 절차](harness/.claude/skills/delegate/git-workflow.md) |
| 마무리와 이해 | 통합 검증·실행 README·RETRO를 마친 뒤 전체 정리와 16문항으로 이해를 점검한다. 약점은 근거 코드·테스트로 복습하고 퀴즈가 제출을 막지 않게 한다 | [마무리](harness/.claude/skills/wrapup/SKILL.md) |
| 증거의 범위 | 자동 검사는 설치·실행기의 동작을 확인한다. 실제 모델의 전체 수행은 별도 리허설로 확인한다. 과거 Claude 기록·비용과 평가 방식의 2차 정보는 현재 실행의 증거가 아니다 | [검사](scripts/check.sh), [평가 정보](docs/01-cofa-probe.md) |

## 이해 점검 퀴즈 — 하네스 사용법 12문항

이 문제는 **이 저장소의 사용법**을 복습하기 위한 것입니다. 설치된 과제에서 생성하는 12·16문항은 그 과제의 실제 도메인·코드·검증을 바탕으로 별도로 만듭니다. 답마다 결론과 이유를 적고, 아래 해설은 답한 뒤 펼치세요. 각 문항은 결론 1점·근거 1점이며, 미응답은 미채점입니다.

1. 유지보수 저장소와 새 과제 폴더가 있다. 배포할 공통 지침은 어디서 고치고, 과제의 SPEC·TASKS는 어디에 만들어야 하는가?
2. 과제 폴더의 `CLAUDE.md`·`.claude/CLAUDE.md` 모두 배포본과 다른 사용자 지침이며, `docs/SPEC.md`에도 작업 내용이 있다. 기본 설치와 `--force` 설치는 각각 무엇을 변경·보존하는가?
3. 셸에 `/kickoff README.md 13:00`을 입력했더니 시작되지 않는다. 어디서 호출해야 하며, 슬라이스 뒤 `/clear`로 넘어가기 전에 무엇을 남겨야 하는가?
4. 페르소나의 답과 실제 샘플의 단위가 서로 다르다. 어느 쪽도 확정할 수 없다면, 무엇을 기록하고 어떻게 다음 질문을 해야 하는가?
5. 기능 후보가 5개이고 구현은 CLI 하나로 충분하다. 첫 구현 전에 무엇을 확정하며, 첫 슬라이스는 어느 수준까지 동작해야 하는가?
6. S1·S2의 선행 의존성은 모두 DONE이고 수정할 코드 파일도 다르지만, 검증에서 같은 DB 파일을 쓴다. 동시에 실행해도 되는가? 가능하게 만들려면 무엇이 달라져야 하는가?
7. 작업자 상태가 `REPORTED_COMPLETE`이고 세션은 이미 끝났다. 바로 TASKS를 DONE으로 바꿀 수 있는가? 루트가 확인할 순서를 설명하라.
8. 시작할 때 사용자가 다른 파일을 이미 staged해 두었다. 이번 슬라이스의 검증은 통과했다. 구현 결과와 Git 인덱스를 어떻게 처리해야 하는가?
9. 사용자가 퀴즈를 푼 뒤 알고리즘이 바뀌었다. KNOWLEDGE와 과거 문제·답·점수를 어떻게 갱신해야 학습 이력을 보존할 수 있는가?
10. S0 테스트는 모두 통과했지만 P0의 저장 기능은 아직 스텁이다. 마무리 요약에서 무엇이 완료됐다고 말할 수 있고, 무엇을 미완료로 남겨야 하는가?
11. 16문항 중 4문항에 답해 6점을 받은 사용자가 `그만`이라고 했다. 점수·남은 문제·다음 행동·제출 상태를 어떻게 안내해야 하는가?
12. 설치 테스트와 가짜 Codex를 쓴 tmux 테스트가 통과했고, 과거 Claude 리허설의 비용표도 있다. 이 자료로 무엇을 확인할 수 있고, 현재 Claude/Codex의 전체 수행·비용과 당일 평가 규칙 중 무엇은 별도 확인이 필요한가?

<details>
<summary>답변 후 펼치기 — 해설과 복습 위치</summary>

1. main의 배포 지침은 `harness/CLAUDE.md`에서 고치고 SPEC·TASKS는 설치 대상 과제의 `docs/`에 만든다. 이 저장소의 docs는 하네스 사용·설계 문서다. [배포 지침](harness/CLAUDE.md)
2. 두 Claude 지침 모두 다르면 기본 설치는 어떤 파일도 쓰기 전에 중단한다. `--force`는 설치 대상으로 선택된 `.claude/CLAUDE.md`와 충돌한 스킬을 백업 후 교체한다. 기존 루트 사용자 지침과 SPEC 등 docs는 보존하고 없는 템플릿만 추가한다. [설치기](scripts/install.py)
3. 과제 루트에서 Claude를 실행하고 그 대화 입력창에 호출한다. Codex는 `--tool codex`로 설치한 뒤 `$kickoff`로 호출하고 `/new`로 새 대화를 연다. 새 대화 전에는 검증 결과·슬라이스 상태·결정과 커밋 또는 보류 사유를 docs에 남겨 파일만으로 재개할 수 있게 한다. [사용 순서](#전체-사용-순서-ai-입력창)
4. 두 해석과 근거를 `domain/README.md`의 미확인 항목에 남기고, 결정을 바꿀 단위를 구체적 사례로 한 번에 하나씩 확인한다. 충돌한 내용을 임의로 확정 사실로 바꾸지 않는다. [인터뷰 정리](harness/.claude/skills/interview/SKILL.md)
5. 근거와 완료 기준이 있는 P0를 최대 3개로 좁히고 비목표·입출력·오류·픽스처·슬라이스 검증을 정한다. 모듈 하나면 계약은 SPEC 8절에 둔다. S0는 입력 하나가 실행부터 출력까지 지나가는 뼈대다. [SPEC 절차](harness/.claude/skills/spec/SKILL.md)
6. 같은 DB를 쓰는 검증은 서로 영향을 줄 수 있어 순차 실행한다. 병렬로 하려면 DB·포트·생성물 등 검증 자원까지 분리하고 쓰기 범위가 겹치지 않아야 한다. [병렬 분할](harness/.claude/skills/delegate/tmux.md)
7. 보고 도착은 작업자의 주장이다. 모든 보고 회수·작업자 정지 → 변경 범위 확인 → 루트의 슬라이스 검증·회귀 확인 → 공유 문서 갱신·DONE 판정 순서다. [회수와 검증](harness/.claude/skills/delegate/tmux.md)
8. 기존 staged 내용은 유지하고 이번 구현·검증 결과를 기록한다. 자동 스테이징·커밋은 보류하고 사유를 알린다. 임의 reset·stash나 다른 파일까지 포함한 커밋을 하지 않는다. [Git 절차](harness/.claude/skills/delegate/git-workflow.md)
9. 실제 코드·테스트를 근거로 KNOWLEDGE와 현재 출제 내용을 갱신한다. 이미 푼 회차의 문제·답·점수는 보존하고 변경 사실과 새 회차·개정 위치를 연결한다. [학습 이력](harness/.claude/skills/interview/learning.md)
10. S0의 검증 통과와 현재 작동하는 경로만 완료로 설명한다. 저장 스텁은 P0 미완료이며 통합 검증 통과나 제출 준비 완료와 같지 않다. 이를 RETRO·전체 정리·문항에 그대로 반영한다. [마무리 검증](harness/.claude/skills/wrapup/SKILL.md)
11. `4/16문항 · 6/8점 · 미응답 12문항`으로 남긴다. 출제를 멈추고 문제·해설·재개 위치와 답한 범위의 약점·복습 행동을 안내한다. 미응답을 오답으로 채점하거나 제출을 미루지 않는다. [채점 기준](harness/.claude/skills/interview/learning.md)
12. 검사한 설치·보존·텍스트 전달·상태 조회 동작과 과거 실행의 기록은 확인할 수 있다. 실제 모델의 전체 구현·퀴즈 진행과 현재 비용은 별도 리허설이 필요하고, 평가 규칙은 당일 안내로 확인한다. [검증 범위](scripts/check.sh), [당일 확인 목록](docs/01-cofa-probe.md)

</details>

다 풀었다면 **과제 설치부터 마무리까지의 흐름, 내가 판단할 지점, 완료를 증명할 근거**를 문서를 덮고 1분 동안 설명해 보세요. 막히는 주제는 해설의 복습 위치로 돌아가면 됩니다.
