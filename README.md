# domain-adaptable-skill

Cofa Probe 환경(크래프톤의 AI 실무 역량 평가 플랫폼)에서 열리는 해커톤을 위한 **개인 하네스**입니다. Claude Code 형식을 원본으로 관리하고, 설치기가 구버전 Claude 명령과 Codex 형식도 생성합니다.
어떤 도메인의 과제가 나와도(웹 서비스, 데이터 파이프라인, EDA 툴 자동화, 사내 자동화 플랫폼) 같은 순서로 일할 수 있게 만들었습니다.

## 30초 설명
Cofa Probe는 결과물만 보지 않습니다. 6시간 동안 **AI와 어떻게 일했는지**(어떤 질문을 했나, 어떻게 쪼개 위임했나, 어떻게 검증했나, AI의 과잉 설계를 통제했나, 토큰을 얼마나 썼나)를 20여 개 평가 에이전트가 기록하고 채점합니다.
이 하네스는 그 평가 방식에 맞는 일하는 순서를 **명령 5개**로 만들고, 과정에서 생기는 지식과 결정을 **`docs/` 폴더의 파일**로 남깁니다. 파일이 남으니 세션을 비워도 안전하고, 토큰이 적게 듭니다. 결정 기록은 명령이 알아서 하고, 명령 하나의 답은 15줄 이내로 짧습니다. 인터뷰가 끝나면 `/interview`가 이어서 도메인 지식을 내 말로 다지고, 요약과 퀴즈로 내가 설명할 수 있는지 확인합니다. 퀴즈는 커밋·푸시를 막지 않습니다.

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
│       ├── interview/             페르소나 질문 생성. 답을 붙이면 정리하고 다음 질문까지, 끝나면 다지기·요약·퀴즈 (+ grill.md)
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
│   └── test_install.py            충돌·재설치·백업·호환 형식·ZIP 검증
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
│   ├── domain/                현업 지식: persona · workflow · constraints · success + 인덱스 (+ 반도체 primer)
│   ├── CONTRACT.md            모듈이 2개 이상일 때만: 모듈 사이 인터페이스 (/spec이 생성)
│   ├── briefs/                위임 브리프 사본 (/delegate가 생성)
│   └── RETRO.md               복기 문서 (/wrapup이 생성)
├── fixtures/                  입출력 샘플 파일 (/spec이 생성)
└── <모듈>/CLAUDE.md           모듈이 2개 이상일 때만, 40줄 이하 지침 (/spec이 생성)
```

## 준비와 설치 (터미널)

설치는 **Bash와 Python 3.8 이상**이 필요합니다(`unzip`이 없으면 Python으로 풉니다). 패키징은 `zip`, 작업에는 Git과 선택한 AI CLI가 필요합니다.

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

Codex 설치기는 명령 표기·템플릿 경로·모듈 지침 이름을 변환하고 사용자 호출 전용 정책을 생성합니다. 이 정책은 [OpenAI 공식 스킬 문서](https://learn.chatgpt.com/docs/build-skills), `/new`는 [공식 CLI 문서](https://learn.chatgpt.com/docs/developer-commands?surface=cli)에 따릅니다. 서브에이전트 도구가 없으면 브리프대로 루트에서 순차 구현합니다. 변환·경로는 자동 테스트하며, 각 CLI 버전의 전체 대화형 흐름은 별도 리허설이 필요합니다.

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
| 4. 다지기·복습 | 인터뷰 종료 뒤 자동 진행 | 동일 | 빈틈 질문에 답하고 퀴즈 풀기. `그만`으로 다지기 종료, 탐색을 끝내려면 다음 계약 명령으로 이동 | 문서의 빈틈 보완. 퀴즈 결과는 저장·제출과 무관 |
| 5. 계약, ~1:20 | `/spec` | `$spec` | 필요한 선택만 결정 | P0≤3, 비목표, 입출력 픽스처, 검증 명령·쓰기 범위가 있는 슬라이스 |
| 6. 뼈대 | `/delegate S0` | `$delegate S0` | 제거 후보·화면 확인 요청이 있으면 답하기 | 입력부터 출력까지 동작하는 뼈대, 검증, 커밋 |
| 7. 구현, ~3:10 | `/delegate S1` → `/clear` → `/delegate S2` … | `$delegate S1` → `/new` → `$delegate S2` … | 슬라이스마다 커밋(또는 보류 사유)이 남은 것을 보고 비운 뒤 TASKS의 다음 P0 ID로. 두 슬라이스쯤 뒤 실제 출력을 페르소나에게 시연 | 브리프 → 구현 → 재검증·회귀 → 정리 → 커밋. 다음 세션은 docs에서 재개 |
| 8. 마무리, 3:10~4:00 | `/wrapup` | `$wrapup` | 화면 확인·정리 후보에 답하고 RETRO 읽기 | 통합 검증, 실행 README, 정리, RETRO, 요약·퀴즈 |

모든 스킬은 **사람이 호출**합니다. Claude는 `disable-model-invocation: true`, Codex는 `allow_implicit_invocation: false`로 설정합니다. 절차는 5개이며 결정 기록은 명령 안에서 자동으로 남깁니다. 순차 슬라이스는 같은 파일을 확장할 수 있고, 병렬 실행할 때만 범위를 분리합니다.

## 선택 기능과 문제 해결

| 상황 | Claude 입력·행동 | Codex 입력·행동 | 처리 |
|---|---|---|---|
| 독립된 작업을 병렬로 | `/delegate S1 --parallel` | `$delegate S1 --parallel` | 의존성·쓰기 범위가 겹치지 않는 TODO만 병렬. 모든 보고 뒤 슬라이스별 검증·커밋 |
| 구현 중 새 요구 | `/interview <답>` → `/spec` → `/delegate <새 ID>` | `$interview <답>` → `$spec` → `$delegate <새 ID>` | 기존 DONE은 유지, 계약·픽스처 갱신 후 새 슬라이스 추가 |
| 계약 변경 BLOCKER | 루트에서 SPEC·CONTRACT·픽스처 수정 후 재위임 | 동일 | 하위 에이전트가 계약을 임의 변경하지 않음 |
| 검증 실패 | 재현 → 원인·수정 파일·검증 방법 확인 → 수정·재검증 | 동일 | 통과 전 DONE·다음 슬라이스 안내 금지 |
| 기존 staged 변경 | 표시된 경로를 확인해 기존 작업을 별도로 처리 | 동일 | 구현·검증은 가능, 자동 스테이징·커밋은 보류. 기존 변경을 되돌리지 않음 |
| 새 범위 밖 변경 | 경로·출처를 확인 | 동일 | 기존 작업을 보존하며 임의 삭제·복구하지 않음 |
| 마무리 검증만 | `/wrapup check` | `$wrapup check` | 검증·화면·README·정리까지만 |
| 마무리 검증 실패 | 시간이 있으면 고친 뒤 `/wrapup` 재실행 | 고친 뒤 `$wrapup` 재실행 | `/wrapup`이 고칠지, 실패를 RETRO 4절에 적고 진행할지 묻는다. 마감이 가까우면 진행 |
| 복기·퀴즈만 요청 | `/wrapup retro` | `$wrapup retro` | 단독 호출도 통합 검증을 먼저 재실행. 실패가 남으면 위와 같이 묻는다 |
| 복습만 | `/interview quiz` | `$interview quiz` | 요약 + 4문항 퀴즈. 파일을 바꾸거나 제출을 막지 않음 |

커밋은 검토한 **개별 파일 경로**만 추가합니다. 기존 staged 변경, 다른 슬라이스의 브리프, 테스트 캐시, 설치 백업을 섞지 않습니다. 공통 절차는 [git-workflow.md](harness/.claude/skills/delegate/git-workflow.md)에 있습니다.

## 세 가지 설계 원칙
### 1. 도메인 지식을 쌓는 구조 (grill-with-docs 방식)
grill-with-docs는 계획을 집요하게 인터뷰하면서 합의된 용어를 `GLOSSARY.md`에, 결정을 ADR에 바로 적는 스킬입니다. 여기서는 인터뷰 상대가 사용자가 아니라 **페르소나 에이전트**이므로, `/interview`가 질문을 만들고, 답을 붙여 실행하면 소화해서 `docs/domain/<주제>.md`, `GLOSSARY.md`, `SPEC.md`에 나눠 적은 뒤 다음 질문을 냅니다. `domain/README.md` 인덱스만 읽어도 무엇을 아는지 보이고, 모듈은 필요한 파일 하나만 엽니다. 결정은 명령이 생길 때마다 `DECISIONS.md` 한 파일에 D-NNN으로 쌓습니다.

인터뷰가 끝나면 `/interview`가 이어서 하는 다지기는 grill-with-docs를 더 그대로 따릅니다. 이번에는 사람에게 직접 묻습니다. 문서의 빈틈(GLOSSARY와 다르게 쓰는 말, 단위·경계, 경계에 걸리는 사례, 문서와 샘플의 모순)을 한 번에 하나씩 추천 답과 함께 묻고, 답은 기존 문서 한 곳에 바로 적습니다. 새 파일은 만들지 않습니다. 끝에는 blindspot의 보고서·퀴즈처럼 쉬운 말 요약과 4문항 퀴즈를 터미널에 냅니다(마감 때는 `/wrapup`이 같은 퀴즈를 냅니다). 퀴즈는 복습용이라 결과를 남기지 않고, 커밋·머지·푸시를 막지 않습니다.

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

**Claude Code 대신 Codex만 있으면?** 설치기에 `--tool codex`를 붙이고 `codex`를 시작하세요. `$kickoff README.md <마감 시각>`부터 위 표대로 진행합니다. 기존 `AGENTS.md`는 자동 덮어쓰지 않습니다. 현재 변환기의 자동 검증과 이전 버전의 CLI 리허설은 구분하며, 실제 위임 도구가 없으면 순차 구현합니다.

**왜 모듈을 많이 안 나누나요?** 나누는 것 자체가 과잉 설계일 수 있습니다. 기본은 1개이고, 검증 방법이 다르거나 병렬로 만들 가치가 있을 때만 나눕니다. 모듈이 1개면 계약(입출력 샘플)은 `SPEC.md` 8절에 두고 `CONTRACT.md`와 모듈 지침은 만들지 않습니다.

**git에 올려도 되나요?** `harness/`는 그대로 커밋해도 됩니다. `dist/`는 `.gitignore`에 있습니다.

## 더 읽기
- [docs/01-cofa-probe.md](docs/01-cofa-probe.md) — 평가 방식과 당일 확인 목록
- [docs/02-strategy.md](docs/02-strategy.md) — 전략 전체
- [docs/03-cheatsheet.md](docs/03-cheatsheet.md) — 한 장 요약
- [docs/04-design-notes.md](docs/04-design-notes.md) — 설계 이유와 확장법
