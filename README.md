# domain-adaptable-skill — Codex

Cofa Probe 환경의 해커톤을 위한 **Codex용 개인 하네스**입니다. `codex` 브랜치는 `AGENTS.md`와 `.agents/skills/`를 원본으로 관리하며, 설치 기본값도 Codex입니다.
웹 서비스, 데이터 파이프라인, EDA 툴 자동화 등 어떤 도메인에서도 **문제 정의 → 인터뷰 → 계약 → 슬라이스 구현·검증 → 복기** 순서로 일합니다.

## 30초 설명

다섯 스킬이 작업 절차를 안내하고, 지식과 결정은 과제 프로젝트의 `docs/`에 남깁니다.
`$interview`는 페르소나에게 물을 질문을 만들고, 답을 정리하며, 인터뷰가 끝나면 다지기·요약·퀴즈를 진행합니다.
`$delegate`는 슬라이스 하나의 브리프·구현·검증·정리·커밋을 끝냅니다. 퀴즈는 제출이나 커밋을 막지 않습니다.

## 폴더 지도

```text
domain-adaptable-skill/
├── AGENTS.md                       이 저장소를 유지보수하는 Codex 지침
├── README.md
├── docs/                           평가 방식·전략·치트시트·설계 노트
├── harness/                        과제 프로젝트에 설치하는 원본
│   ├── AGENTS.md                   공통 규칙·작은 코드 원칙·Git 변경 보존
│   └── .agents/skills/
│       ├── kickoff/                과제 재정의·시간 계획·docs 템플릿
│       ├── interview/              현업 질문·답 정리·다지기·퀴즈
│       ├── spec/                   SPEC·계약·픽스처·모듈 AGENTS 템플릿
│       ├── delegate/               브리프·위임·검증·정리·커밋
│       └── wrapup/                 통합 검증·README·RETRO·퀴즈
├── scripts/
│   ├── install.sh / install.py     Codex 설치·백업, 선택적 Claude 호환 변환
│   ├── pack.sh                    dist/harness.zip 설치 키트 생성
│   ├── check.sh                   줄 수·메타데이터·참조·설치 회귀 검사
│   └── test_install.py            원본 복사·충돌·보존·호환·ZIP 검증
└── examples/                       과거 리허설 기록과 직접 연습할 과제 키트
```

각 스킬에는 `SKILL.md`와 `agents/openai.yaml`이 있습니다. 원래의 사용자 호출 전용 정책(`allow_implicit_invocation: false`)을 유지합니다.
Codex는 프로젝트의 `.agents/skills/`에서 스킬을 찾고 `$이름`으로 호출할 수 있습니다. [OpenAI 공식 스킬 문서](https://learn.chatgpt.com/docs/build-skills)

설치된 과제 프로젝트에는 다음 파일이 생깁니다.

```text
<과제 프로젝트>/
├── AGENTS.md
├── .agents/skills/…                다섯 스킬과 참고 파일
├── docs/
│   ├── SPEC.md                     목표·P0/P1/P2·비목표·입출력 샘플
│   ├── TASKS.md                    시간표·슬라이스·검증 명령·BLOCKER
│   ├── DECISIONS.md                결정과 거절한 AI 제안
│   ├── GLOSSARY.md                 현업 용어
│   └── domain/                    persona·workflow·constraints·success·primer
├── fixtures/                       $spec이 생성하는 입출력 샘플
└── <모듈>/AGENTS.md                모듈이 여럿일 때 $spec이 생성
```

`docs/CONTRACT.md`는 모듈이 여럿일 때, `docs/briefs/`는 위임할 때, `docs/RETRO.md`는 마무리할 때 생성합니다.
이 저장소 루트의 `AGENTS.md`는 유지보수용이고, 설치되는 것은 `harness/AGENTS.md`입니다.

## 준비와 설치 (터미널)

Bash와 Python 3.8 이상이 필요합니다. 패키징에는 `zip`, 작업에는 Git과 Codex CLI가 필요합니다.

```bash
# 이 저장소에서 검사한 뒤, 이미 존재하는 과제 폴더에 설치
bash scripts/check.sh
bash scripts/install.sh /path/to/task

# 과제 폴더에서 시작
cd /path/to/task
codex
```

기본 설치는 Codex이며 `--tool codex`를 명시해도 같습니다. 과제 폴더에서 첫 커밋을 만든 뒤 Codex 입력창에 `$kickoff README.md 13:00`을 입력합니다.

### ZIP으로 반입하기

이 저장소에서 `bash scripts/pack.sh`를 실행해 `dist/harness.zip`을 만듭니다.
과제 루트에 ZIP을 올리고 아래 블록으로 설치합니다. 프로젝트에 직접 압축을 풀지 않습니다.

```bash
HARNESS_KIT=$(mktemp -d)
unzip -q harness.zip -d "$HARNESS_KIT" || python3 -m zipfile -e harness.zip "$HARNESS_KIT"
bash "$HARNESS_KIT/scripts/install.sh" "$PWD" && rm harness.zip
```

설치가 성공한 뒤 초기 자료를 검토해 첫 커밋을 만듭니다. 아래 블록은 새 과제 폴더 기준입니다.
기존 저장소라면 먼저 `git status --short`로 기존 변경·스테이징을 확인하고, 실제 존재하는 초기 자료만 추가합니다.

```bash
git rev-parse --git-dir >/dev/null 2>&1 || git init
git config user.email >/dev/null || git config user.email "me@example.com"
git config user.name  >/dev/null || git config user.name "이름"
git add -- README.md AGENTS.md .agents/ docs/    # + 검토한 과제 파일
git diff --cached --stat && git commit -qm "init: 과제와 Codex 하네스"
codex
```

| 설치 상황 | 동작 |
|---|---|
| 새 프로젝트 / 같은 버전 재설치 | 없는 파일만 생성 / 동일 파일 건너뜀 |
| 기존 `AGENTS.md`·스킬·호출 정책과 내용 충돌 | 파일을 쓰기 전에 종료코드 2로 중단하고 경로 표시 |
| `--force`로 갱신 | 충돌 파일을 `.harness-backups/<시각-고유값>/`에 백업 후 교체 |
| 기존 `docs/` 작업 상태 | `--force`여도 보존하고 없는 템플릿만 추가 |
| 심볼릭 링크·잘못된 파일 경로 | 변경 전에 중단 |

충돌 시 기존 내용과 배포본을 비교해 병합하거나, 백업 후 교체하려면 같은 설치 명령에 `--force`를 붙입니다. 백업은 커밋에서 제외합니다.

## 전체 사용 순서 (Codex 입력창)

아래 스킬 호출은 **셸이 아닌 Codex 대화 입력창**에 입력합니다. 셸에서 `$kickoff`를 입력하면 환경변수로 해석됩니다.
작업 위치는 과제 프로젝트 루트입니다. 아래 시간은 4시간 기준이며, 마감은 한국 시각입니다.

| 순서·시간 | 입력 | 할 일·결과 |
|---|---|---|
| 시작 | `$kickoff README.md 13:00` | SPEC 초안·열린 질문·TASKS 시간표. `3h45m`도 가능, 생략 시 6시간 |
| 탐색 ~0:40 | `$interview` | 질문 3~5개를 본인 말로 바꿔 페르소나에게 묻기 |
| 답 정리 반복 | `$interview <답변>` | domain·GLOSSARY·SPEC 갱신 + 다음 질문 |
| 다지기·복습 | 인터뷰 종료 뒤 자동 진행 | 빈틈 질문 → 요약 → 퀴즈. `그만`으로 종료 가능 |
| 계약 ~1:20 | `$spec` | P0≤3·비목표·픽스처·슬라이스·검증 명령 확정 |
| 뼈대 | `$delegate S0` | 입력부터 출력까지 흐르는 뼈대·검증·커밋 |
| 구현 ~3:10 | `$delegate S1` → `/new` → `$delegate S2` | 구현·검증·정리·커밋. 두 슬라이스쯤 뒤 실제 출력 시연 |
| 마무리 3:10~4:00 | `$wrapup` | 통합 검증·실행 README·정리·RETRO·요약·퀴즈 |

커밋 또는 보류 사유가 `docs/`에 남은 뒤 `/new`로 새 대화를 시작하고 파일에서 재개합니다. [OpenAI 공식 명령 문서](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
모듈별 지침은 `<모듈>/AGENTS.md`에 두며, 루트에서 위임할 때도 관련 지침을 브리프에 포함합니다. [AGENTS.md 공식 문서](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

## 선택 기능과 문제 해결

| 상황 | 입력·처리 |
|---|---|
| 독립 작업 병렬 구현 | `$delegate S1 --parallel`. 의존성·쓰기 범위가 겹치지 않는 TODO만 병렬 |
| 서브에이전트 도구 없음·위임 불가 | 같은 브리프와 검증 규칙으로 루트에서 순차 구현 |
| 구현 중 새 요구 | `$interview <답>` → `$spec` → `$delegate <새 ID>`. 기존 DONE은 유지 |
| 계약 변경 BLOCKER | 루트에서 SPEC·CONTRACT·픽스처 갱신 후 재위임 |
| 검증 실패 | 재현 → 원인·수정 파일·검증 방법 → 수정·재검증. 통과 전 DONE 금지 |
| 기존 staged 변경 | 구현·검증은 진행하되 자동 스테이징·커밋 보류. 기존 작업 보존 |
| 검증만 / 복기만 | `$wrapup check` / `$wrapup retro`. retro 단독도 통합 검증부터 |
| 복습만 | `$interview quiz`. 퀴즈는 파일·제출 상태를 바꾸지 않음 |
| 스킬이 안 보임 | 과제 루트의 `.agents/skills/*/SKILL.md` 확인, `/skills` 또는 `$`로 선택, 필요하면 Codex 재시작 |
| 지침이 다르게 적용됨 | 해당 폴더와 상위 경로의 `AGENTS.override.md` 확인. 사용자 지침과 병합 |
| 하네스 반입 불가 | [치트시트](docs/03-cheatsheet.md)의 최소 AGENTS.md 사용 |

커밋은 검토한 개별 파일만 추가하고, 다른 슬라이스의 브리프·캐시·설치 백업은 섞지 않습니다. [공통 Git 절차](harness/.agents/skills/delegate/git-workflow.md)

## 설계와 검증

- 지식은 `docs/domain/`과 `GLOSSARY.md`, 결정은 `DECISIONS.md`에 기록합니다.
- `AGENTS.md`의 작은 코드 원칙으로 불필요한 기능·추상화를 줄이고, 입력 검증·데이터 보호·보안·접근성은 유지합니다.
- 공통 지침은 80줄, 스킬 본문은 120줄, 참고 파일은 80줄 이내로 유지합니다. 필요한 파일만 읽고 세션 상태는 문서에 남깁니다.
- `scripts/check.sh`는 줄 수·프런트매터·호출 정책·참조·설치 테스트를 검사합니다. 토큰 수는 바이트 기반 근사이며 전체 세션 비용이 아닙니다.
- 설치 테스트는 기존 문서 보존·충돌·백업·재설치·Claude 호환·ZIP 설치 동등성을 검증합니다. 실제 AI의 인터뷰·위임·퀴즈 동작은 별도 리허설 대상입니다.

## Claude 호환 설치

필요하면 Codex 원본에서 호환 형식을 생성할 수 있습니다.

| 도구 | 설치 옵션 | 설치 파일 | 호출 / 새 세션 |
|---|---|---|---|
| Codex (기본) | 생략 또는 `--tool codex` | `AGENTS.md`, `.agents/skills/` | `$kickoff` / `/new` |
| Claude Code | `--tool claude` | `CLAUDE.md`, `.claude/skills/` | `/kickoff` / `/clear` |
| 구버전 Claude | `--tool claude-commands` | 위 파일 + 링크를 보정한 `.claude/commands/*.md` | `/kickoff` / `/clear` |

Claude 설치 시 기존 루트 `CLAUDE.md`가 사용자 지침이면 하네스는 `.claude/CLAUDE.md`에 설치합니다. 두 파일 모두 충돌하면 쓰기 전에 중단합니다.
Claude 원본과 이전 변경 이력은 `main` 브랜치에서 확인할 수 있습니다.

## 미리 연습하기

- [리허설 3 키트](examples/rehearsal-3-yield-kit/README.md): 다섯 스킬을 Codex로 직접 연습합니다. `persona.md`와 `after-rehearsal/`은 끝난 뒤에 읽습니다.
- `examples/rehearsal-interview-coach/`와 `examples/rehearsal-2-regress-triage/`는 **이전 Claude 버전의 실행 기록**입니다. 대화·코드·비용·자동 실행 스크립트는 당시 증거로 보존하며 Codex 검증 결과가 아닙니다.
- 반도체 사전 지식은 `harness/.agents/skills/kickoff/templates/docs/domain/primer.md`에 있습니다. 다른 도메인이라면 해당 내용을 바꿀 수 있습니다.

## 더 읽기

- [평가 방식과 당일 확인 목록](docs/01-cofa-probe.md)
- [전체 전략](docs/02-strategy.md)
- [당일 치트시트](docs/03-cheatsheet.md)
- [설계 노트와 변환 기록](docs/04-design-notes.md)
