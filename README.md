# domain-adaptable-skill — Codex

Cofa Probe 환경의 해커톤을 위한 **Codex용 개인 하네스**입니다. `codex` 브랜치는 `AGENTS.md`와 `.agents/skills/`를 원본으로 관리하며, 설치 기본값도 Codex입니다.
웹 서비스, 데이터 파이프라인, EDA 툴 자동화 등 어떤 도메인에서도 **문제 정의 → 인터뷰 → 계약 → 슬라이스 구현·검증 → 복기** 순서로 일합니다.

## 30초 설명

다섯 스킬이 작업 절차를 안내하고, 지식과 결정은 과제 프로젝트의 `docs/`에 남깁니다.
`$interview`는 페르소나에게 물을 질문을 만들고, 답을 정리하며, 인터뷰가 끝나면 다지기·요약·확인 4문항으로 마칩니다.
`$spec`은 구현 계획을 10줄로 보여 주고 의견을 반영한 뒤 확정합니다. `$delegate`는 작은 브리프를 tmux의 비대화형 작업자에 전달하고, 독립 작업은 필요할 때 병렬로 처리합니다. 마일스톤의 구현 방식을 확인하고 루트에서 검증·정리·커밋합니다.
깊은 복습은 `$interview quiz`(12문항), 마무리는 16문항입니다. 학습 문서는 이 두 시점에만 써서 구현 중의 시간과 토큰을 아낍니다. 마지막에는 문제 정의·전체 동작·알고리즘·선택 이유·검증·한계를 정리하고, 모든 P0와 학습 주제를 문제·해설·근거에 연결합니다. 퀴즈는 제출이나 커밋을 막지 않습니다.

## 대회 모델과 토큰 사용

허용 모델은 **Sol 6.1·Sol 6.0·Terra 5.6·Luna 6.0**입니다. 설계는 **Sol 6.1 high**, 일반 구현은 **Sol 6.1 medium**으로 시작합니다. Luna는 정해진 치환·서식 수정·추출에 한정하고, 테스트·검색·집계는 루트가 도구로 직접 처리합니다.

| 역할 / 실행기 tier | Codex 모델 ID | 추론 기본값 | 용도 |
|---|---|---|---|
| 루트(설계) | `gpt-6.1-sol` | high | 요구사항·계약·설계·통합 판단 |
| `implement` (기본) | `gpt-6.1-sol` | medium | 기능·UI·테스트 등 일반 구현 |
| `light` | `gpt-6-luna` | medium | 정해진 치환·서식 수정·추출. 기능 판단은 맡기지 않음 |
| `reason` | `gpt-6.1-sol` | high | 구조·알고리즘·복잡한 진단·보안·데이터 무결성 |
| `fallback` | `gpt-6-sol` | medium | Sol 6.1 사용 불가 또는 품질을 확인한 반복 구현 |
| `legacy` | `gpt-5.6-terra` | medium | 기존 패턴을 따르는 국소 수정에서 품질을 확인한 경우 |

2026-11-04에 확인한 공식 표준 크레딧 요금에서 Sol 6.0은 Sol 6.1보다 일반 입력·출력이 저렴하지 않고, Terra 5.6의 출력 요금은 더 높습니다. 그래서 버전순 승급을 만들지 않았습니다. **대회 자체 과금은 별도**이며, 원시 토큰 절감과 모델별 비용 절감은 같은 지표가 아닙니다. [공식 요금표](https://learn.chatgpt.com/docs/pricing)

```bash
# 과제 프로젝트에서 루트 시작 (전역 설정을 덮어쓰지 않음)
codex -m gpt-6.1-sol -c 'model_reasoning_effort="high"'
# 복잡한 슬라이스만 올리기
python3 .agents/skills/delegate/scripts/tmux_codex.py start \
  --project "$PWD" --id S1 --brief docs/briefs/S1.md --tier reason
# 실패·재실행을 포함한 관측 토큰
python3 .agents/skills/delegate/scripts/tmux_codex.py usage --project "$PWD"
```

루트는 `/model`, 작업자는 `--tier`와 필요 시 `--effort low|medium|high`로 선택합니다. `--model`은 모델만 바꾸며 tier의 추론 강도는 유지합니다. Codex 실행기는 허용 목록 밖 모델을 시작 전에 차단합니다. 기본값 원본은 실행기의 `TIERS`입니다.

토큰은 문맥 중복·긴 출력·불필요한 호출에서 줄입니다. 공통 지침은 5,000바이트 이내로 검사하고, 작업자는 작은 브리프로 시작하되 관련 계약·제약·호출부·테스트는 필요한 만큼 확인합니다. 기본 1개, `--parallel`이면 독립 작업 2개입니다. 새 근거 없이 같은 원인의 실패를 반복하면 원인·시도·diff를 붙여 `reason`으로 한 번만 재위임하고, 이미 high였다면 루트가 문맥과 범위를 다시 확인합니다. DONE 전 P0 수용 조건·사용자 흐름·오류 처리까지 확인하고, 전체 회귀는 통합 체크포인트와 마무리에 수행합니다. [모델·문맥·재시도 규칙](harness/.agents/skills/delegate/routing.md)

`usage`는 Codex 완료 턴의 입력·캐시 입력·출력을 모델/추론별 집계합니다. 캐시 입력은 입력에 이미 포함되며 합계는 입력+출력입니다. 긴 이벤트는 파일에 두고 부모에는 보고와 집계만 전달합니다. `unknown_runs`·`errors`도 확인하세요. 루트·다른 CLI·완료 이벤트가 없는 실패 중 사용량은 이 집계에 포함되지 않습니다. [공식 JSON 이벤트 형식](https://learn.chatgpt.com/docs/non-interactive-mode)

이 설정은 실제 모델의 결과물 품질이나 완료당 최소 토큰을 입증한 벤치마크는 아닙니다. **품질 기준을 통과한 결과의 재작업 포함 토큰**으로 비교합니다. 기본 구현은 Sol 6.1을 쓰고, 같은 유형에서 결과가 충분하다고 확인한 작업만 경량 모델로 옮깁니다. high는 설계·복잡한 추론에 집중합니다. [모델·추론 선택](https://learn.chatgpt.com/docs/models)

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
│   └── test_*.py                  설치·보존·호환·ZIP·tmux 텍스트 전달 검증
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
│   ├── KNOWLEDGE.md                전체 정리·필수 지식·알고리즘·실행 예·대안
│   ├── QUIZ.md                     복습 12문항·마무리 16문항·주제 연결·복습 위치
│   ├── QUIZ-ANSWERS.md             별도 풀이·근거·채점 기준
│   └── domain/                    persona·workflow·constraints·success·primer
├── fixtures/                       $spec이 생성하는 입출력 샘플
└── <모듈>/AGENTS.md                모듈이 여럿일 때 $spec이 생성
```

`docs/CONTRACT.md`는 모듈이 여럿일 때, `docs/briefs/`는 위임할 때, `docs/RETRO.md`는 마무리할 때 생성합니다.
이 저장소 루트의 `AGENTS.md`는 유지보수용이고, 설치되는 것은 `harness/AGENTS.md`입니다.

## 준비와 설치 (터미널)

Bash와 Python 3.8 이상이 필요합니다. 패키징에는 `zip`, 작업에는 Git과 Codex CLI가 필요합니다. 병렬 작업에는 `tmux`와 로그인된 Codex CLI가 필요합니다.

```bash
# 이 저장소에서 검사한 뒤, 이미 존재하는 과제 폴더에 설치
bash scripts/check.sh
bash scripts/install.sh /path/to/task

# 과제 폴더에서 시작
cd /path/to/task
codex -m gpt-6.1-sol -c 'model_reasoning_effort="high"'
```

기본 설치는 Codex이며 `--tool codex`를 명시해도 같습니다. 과제 폴더에서 첫 커밋을 만든 뒤 Codex 입력창에 `$kickoff README.md 13:00`을 입력합니다.

Codex를 샌드박스 모드(read-only·workspace-write)로 쓰면 `.git`이 읽기 전용이고 tmux 소켓 접속도 막힙니다. 그래서 하네스의 커밋과 병렬 실행기 시작 때 권한 상승 승인을 요청받습니다. 승인하면 그대로 진행하고, 거절하면 커밋은 보류되고 병렬 구현은 내장 서브에이전트나 순차 구현으로 바뀝니다. 현재 정책은 `/status`, 묻지 않고 허용할 범위는 `/permissions`에서 대회 규칙 안에서 정합니다.

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
codex -m gpt-6.1-sol -c 'model_reasoning_effort="high"'
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
| 다지기·확인 | 인터뷰 종료 뒤 자동 진행 | 빈틈 질문 → 요약 → 확인 4문항(파일 없음). 깊은 복습은 `$interview quiz` |
| 계약 ~1:20 | `$spec` | P0≤3·비목표·픽스처·슬라이스·검증 명령 확정 → 구현 계획 10줄을 보고 의견 반영 |
| 뼈대 | `$delegate S0` | 입력부터 출력까지 흐르는 뼈대·검증·커밋 |
| 구현 ~3:10 | `$delegate S1` → `/new` → 다음 TODO | 마일스톤(S0·P0 첫 슬라이스·대안 있는 알고리즘)은 방식 확인 후 진행. 일반 작업은 Sol 6.1 medium으로 구현, `--parallel`이면 독립 작업 병렬, 루트에서 슬라이스별 검증·정리·커밋. P0가 끝나면 시연·의견 |
| 마무리 3:10~4:00 | `$wrapup` | 통합 검증·실행 README·RETRO·전체 정리·16문항 퀴즈 |

커밋 또는 보류 사유가 `docs/`에 남은 뒤 `/new`로 새 대화를 시작하고 파일에서 재개합니다. [OpenAI 공식 명령 문서](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
모듈별 지침은 `<모듈>/AGENTS.md`에 두며, 루트에서 위임할 때도 관련 지침을 브리프에 포함합니다. [AGENTS.md 공식 문서](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

## 선택 기능과 문제 해결

| 상황 | 입력·처리 |
|---|---|
| 독립 작업 병렬 구현 | `$delegate S1 --parallel`. 선행 의존성이 DONE이고 쓰기 파일·검증 자원이 분리된 2개, 필요할 때 최대 6개. 기본 호출은 1개 |
| 한 슬라이스만 순차 구현 | `$delegate S1 --serial` |
| 검증·단순 수정만 위임 | 테스트 명령은 루트가 직접. 정해진 치환·추출만 `--tier light`(`gpt-6-luna`, medium) |
| tmux·작업자 CLI 없음 또는 실행 불가 | 사유를 알리고 내장 서브에이전트에 같은 브리프와 등급 모델로 위임, 그것도 없으면 루트에서 순차 구현 |
| 샌드박스가 커밋·실행기를 막음 | 권한 상승 승인 요청에 답한다. 거절하면 커밋은 보류, 병렬은 서브에이전트나 순차 구현 |
| 구현 중 새 요구 | `$interview <답>` → `$spec` → `$delegate <새 ID>`. 기존 DONE은 유지 |
| 계약 변경 BLOCKER | 루트에서 SPEC·CONTRACT·픽스처 갱신 후 재위임 |
| 검증 실패 | 재현 → 원인·수정 파일·검증 방법 → 수정·재검증. 통과 전 DONE 금지 |
| 기존 staged 변경 | 구현·검증은 진행하되 자동 스테이징·커밋 보류. 기존 작업 보존 |
| 검증만 / 복기만 | `$wrapup check` / `$wrapup retro`. retro 단독도 통합 검증부터 |
| 복습만 | `$interview quiz`. KNOWLEDGE·QUIZ·QUIZ-ANSWERS를 갱신하고 12문항. SPEC·TASKS·제출 상태는 유지 |
| 스킬이 안 보임 | 과제 루트의 `.agents/skills/*/SKILL.md` 확인, `/skills` 또는 `$`로 선택, 필요하면 Codex 재시작 |
| 지침이 다르게 적용됨 | 해당 폴더와 상위 경로의 `AGENTS.override.md` 확인. 사용자 지침과 병합 |
| 하네스 반입 불가 | [치트시트](docs/03-cheatsheet.md)의 최소 AGENTS.md 사용 |

커밋은 검토한 개별 파일만 추가하고, 다른 슬라이스의 브리프·캐시·설치 백업은 섞지 않습니다. [공통 Git 절차](harness/.agents/skills/delegate/git-workflow.md)

### 병렬 실행과 학습 문서

[tmux 실행 절차](harness/.agents/skills/delegate/tmux.md)의 실행기가 브리프와 모듈 지침 전문을 초기 프롬프트로 전달합니다. 실행기는 설치된 스킬 폴더로 작업자 CLI를 고르고(Codex: `codex exec --yolo --json -m gpt-6.1-sol`, Claude: `claude -p --model opus`), 작업자가 스스로 읽지 않는 쪽의 루트 지침만 자동으로 더합니다. `--yolo`와 `bypassPermissions`는 승인과 샌드박스를 끄므로 허용된 작업 환경에서 사용합니다. [공식 CLI 옵션](https://learn.chatgpt.com/docs/cli/reference)
실행기는 같은 프로젝트의 세션을 최대 6개로 제한합니다. 기본 위임은 1개이며, `--parallel`은 독립 작업 2개, 시간상 이득이 분명하면 6개까지 늘립니다. 작업자는 보고를 마치면 스스로 끝나며, 보고 없이 끝나 원인 확인용으로 남은 세션은 종료 전까지 한도에 포함됩니다. 비대화형 실행이라 처음 보는 폴더의 신뢰 확인 화면에서 멈추지 않습니다.
부모 에이전트(루트)는 셸 `sleep`으로 주기 조회하지 않고, 결과나 문제가 생길 때까지 기다리는 명령을 씁니다.

```bash
python3 .agents/skills/delegate/scripts/tmux_codex.py wait --project "$PWD" --timeout 60
```

`wait`는 보고 도착·실패·보고 없는 종료·`blocked` 진입이 있거나, 실행 중인 작업이 없거나, 60초가 지나면 `changed`·`running`·`timed_out`과 작업별 상태를 JSON으로 돌려줍니다. 단계·메시지 갱신으로는 깨지 않으므로 작업자가 많아도 부모가 자주 깨지 않고, 진행 상황은 시간 초과 때 한꺼번에 봅니다. 터미널 출력은 싣지 않아 루트 컨텍스트가 덜 쌓입니다. 오래 멈췄거나 실패한 작업만 `status --id S1 --tail 40`으로 화면을 봅니다. 보고 없이 끝난 작업은 원인 확인용으로 화면이 10분 남습니다.
작업자는 단계 전환과 긴 작업의 도구 호출 사이에 전용 `progress.json`을 갱신하고, 질문이 필요하면 입력을 기다리지 않고 BLOCKED로 보고합니다. 갱신 시각은 마지막 보고 시점이며 생존 신호가 아닙니다.
작업자는 겹치지 않는 코드와 전용 진행·보고 파일을 쓰고, 루트는 모든 보고를 회수해 세션을 멈춘 뒤 공유 문서·통합 검증·커밋을 처리합니다. `REPORTED_COMPLETE`는 작업자 보고 도착이며, 루트 검증 후 DONE으로 판정합니다. `FAILED`는 CLI 비정상 종료, `STOPPED`는 보고 없는 종료를 나타냅니다.

[학습 문서·출제 기준](harness/.agents/skills/interview/learning.md)에 따라 `$interview quiz`와 `$wrapup`에서만 실제 알고리즘·자료구조, 입력의 단계별 추적, 시간·공간 복잡도, 불변식, 반례, 대안과 실패 진단을 기록합니다. 복습 12문항·마무리 16문항 중 절반 이상은 서술·계산·추적이며, 4문항씩 답을 받습니다. 문항별 0~2점과 약점 보충 최대 2문항을 적용하고, 문제와 해설을 분리합니다. `그만`이면 남은 학습을 문서에 남깁니다.

마무리의 `KNOWLEDGE.md` 0절은 **문제와 목표 / 도메인과 제약 / 전체 동작 / 핵심 처리 / 선택과 대안 / 실행과 검증 / 한계와 다음 행동**을 근거와 함께 정리합니다. `RETRO.md` 9절과 대화에는 이를 7문장 이내로 요약합니다. `QUIZ.md`의 범위표로 일곱 주제와 모든 P0가 문항에 연결됐는지 확인하며, 마지막 문항은 전체 흐름을 자기 말로 설명하고 달라진 조건에 적용하는 문제입니다.

답하지 않은 문항은 미채점입니다. 예를 들어 16문항 중 4개를 풀어 6점을 받았다면 `4/16문항 · 6/8점 · 미응답 12문항`으로 기록합니다. 주제별로 설명 확인·보충 필요·미응답을 구분하고 다음 복습 행동을 남깁니다. 구현이 바뀌어도 이미 푼 회차의 답·점수는 보존하며, 현재 문제·해설은 새 회차·개정으로 연결합니다.

## 설계와 검증

- 현장 지식은 `docs/domain/`·`GLOSSARY.md`, 필수 지식과 알고리즘은 `KNOWLEDGE.md`, 문제·해설은 `QUIZ.md`·`QUIZ-ANSWERS.md`, 결정은 `DECISIONS.md`에 기록합니다.
- `AGENTS.md`의 작은 코드 원칙으로 불필요한 기능·추상화를 줄이고, 입력 검증·데이터 보호·보안·접근성은 유지합니다.
- 공통 지침은 80줄·5,000바이트, 스킬 본문은 120줄, 참고 파일은 80줄 이내로 유지합니다. 필요한 파일만 읽고 세션 상태는 문서에 남깁니다.
- `scripts/check.sh`는 줄 수·상시 문맥 크기·프런트매터·호출 정책·참조·설치 테스트를 검사합니다. 바이트/4 값은 크기 비교용이며 실제 토큰 수가 아닙니다. 작업자 토큰은 `usage`로 별도 집계합니다.
- 설치 테스트는 학습 문서를 포함한 기존 문서 보존·충돌·백업·재설치·Claude 호환·ZIP 동등성을 검증합니다. tmux가 있으면 가짜 Codex·Claude CLI로 텍스트 전달·허용 모델·등급/추론 선택·캐시 중복 없는 토큰 집계·실패/재실행 집계·6개 동시 실행과 초과 차단·부모의 `wait`·`status` 조회·실패 화면 보존·루트 지침 중복 방지·보고와 실패 구분도 검사합니다. 실행 캐시(`__pycache__`)가 설치·ZIP에 섞이지 않는지도 확인합니다. 실제 모델의 구현 품질과 퀴즈 진행은 별도 리허설 대상입니다.

## Claude 호환 설치

필요하면 Codex 원본에서 호환 형식을 생성할 수 있습니다.

| 도구 | 설치 옵션 | 설치 파일 | 호출 / 새 세션 |
|---|---|---|---|
| Codex (기본) | 생략 또는 `--tool codex` | `AGENTS.md`, `.agents/skills/` | `$kickoff` / `/new` |
| Claude Code | `--tool claude` | `CLAUDE.md`, `.claude/skills/` | `/kickoff` / `/clear` |
| 구버전 Claude | `--tool claude-commands` | 위 파일 + 링크를 보정한 `.claude/commands/*.md` | `/kickoff` / `/clear` |

Claude 설치 시 기존 루트 `CLAUDE.md`가 사용자 지침이면 하네스는 `.claude/CLAUDE.md`에 설치합니다. 두 파일 모두 충돌하면 쓰기 전에 중단합니다.
Claude 설치의 기본 구현은 `opus` medium, 기계적 수정은 `sonnet` medium, 설계·복잡한 작업은 `opus` high입니다. Codex 작업자는 `--worker codex`로 선택합니다. tmux·CLI가 없으면 Agent 도구(general-purpose)에 같은 브리프·모델·추론을 전달하고, 그것도 없으면 루트에서 직접 처리합니다. Markdown 변환은 Sol 두 모델을 `opus`, Luna와 Terra를 `sonnet`으로 바꾸며 실행기와의 일치 여부를 검사합니다. 이번 대회 정책은 codex 브랜치에 적용했으며 main 원본과의 파일 동등성을 주장하지 않습니다.
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

## 전체 내용 정리

이 하네스의 목표는 사용자가 **무엇을 왜 만들었으며, 실제로 어디까지 동작하는지** 근거를 들어 설명하도록 돕는 것입니다.

| 주제 | 기억할 내용 | 다시 볼 곳 |
|---|---|---|
| 저장소와 설치 | 이 저장소는 배포 원본이다. 과제 폴더에 설치하며, 충돌은 쓰기 전에 중단한다. `--force`는 백업 후 지침·스킬을 교체하고 기존 docs는 보존한다 | [설치기](scripts/install.py) |
| 문제 정의 | kickoff에서 모르는 것을 찾고, interview에서 관찰·불편·데이터·성공·가설 순서로 확인한다. 사실·가정·미확인을 구분한다 | [인터뷰](harness/.agents/skills/interview/SKILL.md) |
| 계약과 작업 분할 | P0는 최대 3개, 모듈은 기본 1개다. 비목표·구체적 입출력·실패 예·픽스처·검증 명령을 먼저 정하고 S0부터 만든다 | [계약](harness/.agents/skills/spec/SKILL.md) |
| 구현과 통합 | 기본 1개, `--parallel`이면 독립 2개(최대 6개). 파일·포트·DB·생성물을 분리한다. 부모는 `wait`로 기다리고 모든 보고 회수·작업자 정지 뒤 검증한다. 설계는 Sol 6.1 high, 일반 구현은 같은 모델 medium, 기계적 수정만 Luna medium을 선택한다. 구현 계획과 마일스톤 방식은 사람이 확인한다 | [위임](harness/.agents/skills/delegate/SKILL.md) |
| 기록과 변경 보존 | 상태·지식·결정은 docs에 남긴다. 기존 변경을 보존하고 검토한 파일만 커밋한다. 기존 staged 변경이 있으면 자동 커밋을 보류한다 | [Git 절차](harness/.agents/skills/delegate/git-workflow.md) |
| 마무리와 이해 | 통합 검증·실행 README·RETRO를 마친 뒤 전체 정리와 16문항으로 이해를 점검한다. 약점은 근거 코드·테스트로 복습하고 퀴즈가 제출을 막지 않게 한다 | [마무리](harness/.agents/skills/wrapup/SKILL.md) |
| 증거의 범위 | 자동 검사는 설치·실행기의 동작을 확인한다. 실제 모델의 전체 수행은 별도 리허설로 확인한다. 과거 Claude 기록·비용과 평가 방식의 2차 정보는 현재 실행의 증거가 아니다 | [검사](scripts/check.sh), [평가 정보](docs/01-cofa-probe.md) |

## 이해 점검 퀴즈 — 하네스 사용법 12문항

이 문제는 **이 저장소의 사용법**을 복습하기 위한 것입니다. 설치된 과제에서 생성하는 12·16문항은 그 과제의 실제 도메인·코드·검증을 바탕으로 별도로 만듭니다. 답마다 결론과 이유를 적고, 아래 해설은 답한 뒤 펼치세요. 각 문항은 결론 1점·근거 1점이며, 미응답은 미채점입니다.

1. 유지보수 저장소와 새 과제 폴더가 있다. 배포할 공통 지침은 어디서 고치고, 과제의 SPEC·TASKS는 어디에 만들어야 하는가?
2. 과제 폴더의 `AGENTS.md`와 `docs/SPEC.md`에 사용자 내용이 있다. 기본 설치와 `--force` 설치는 각각 무엇을 변경·보존하는가?
3. 셸에 `$kickoff README.md 13:00`을 입력했더니 시작되지 않는다. 어디서 호출해야 하며, 슬라이스 뒤 `/new`로 넘어가기 전에 무엇을 남겨야 하는가?
4. 페르소나의 답과 실제 샘플의 단위가 서로 다르다. 어느 쪽도 확정할 수 없다면, 무엇을 기록하고 어떻게 다음 질문을 해야 하는가?
5. 기능 후보가 5개이고 구현은 CLI 하나로 충분하다. 첫 구현 전에 무엇을 확정하며, 첫 슬라이스는 어느 수준까지 동작해야 하는가?
6. S1·S2의 선행 의존성은 모두 DONE이고 수정할 코드 파일도 다르지만, 검증에서 같은 DB 파일을 쓴다. 동시에 실행해도 되는가? 가능하게 만들려면 무엇이 달라져야 하는가?
7. 작업자 상태가 `REPORTED_COMPLETE`이고 세션은 이미 끝났다. 바로 TASKS를 DONE으로 바꿀 수 있는가? 루트가 확인할 순서를 설명하라.
8. 시작할 때 사용자가 다른 파일을 이미 staged해 두었다. 이번 슬라이스의 검증은 통과했다. 구현 결과와 Git 인덱스를 어떻게 처리해야 하는가?
9. 사용자가 퀴즈를 푼 뒤 알고리즘이 바뀌었다. KNOWLEDGE와 과거 문제·답·점수를 어떻게 갱신해야 학습 이력을 보존할 수 있는가?
10. S0 테스트는 모두 통과했지만 P0의 저장 기능은 아직 스텁이다. 마무리 요약에서 무엇이 완료됐다고 말할 수 있고, 무엇을 미완료로 남겨야 하는가?
11. 16문항 중 4문항에 답해 6점을 받은 사용자가 `그만`이라고 했다. 점수·남은 문제·다음 행동·제출 상태를 어떻게 안내해야 하는가?
12. 설치 테스트와 가짜 Codex를 쓴 tmux 테스트가 통과했고, 과거 Claude 리허설의 비용표도 있다. 이 자료로 무엇을 확인할 수 있고, 현재 Codex의 전체 수행·비용과 당일 평가 규칙 중 무엇은 별도 확인이 필요한가?

<details>
<summary>답변 후 펼치기 — 해설과 복습 위치</summary>

1. 배포 지침은 `harness/AGENTS.md`에서 고치고 SPEC·TASKS는 설치 대상 과제의 `docs/`에 만든다. 루트 AGENTS는 이 저장소의 유지보수 지침이다. [저장소 규칙](AGENTS.md)
2. AGENTS 내용이 다르면 기본 설치는 어떤 파일도 쓰기 전에 중단한다. `--force`는 충돌한 지침·스킬을 백업 후 교체하지만 기존 SPEC 등 docs는 그대로 보존하고 없는 템플릿만 추가한다. [설치기](scripts/install.py)
3. 과제 루트에서 Codex를 실행하고 그 대화 입력창에 호출한다. 새 대화 전에는 검증 결과·슬라이스 상태·결정과 커밋 또는 보류 사유를 docs에 남겨 파일만으로 재개할 수 있게 한다. [사용 순서](#전체-사용-순서-codex-입력창)
4. 두 해석과 근거를 `domain/README.md`의 미확인 항목에 남기고, 결정을 바꿀 단위를 구체적 사례로 한 번에 하나씩 확인한다. 충돌한 내용을 임의로 확정 사실로 바꾸지 않는다. [인터뷰 정리](harness/.agents/skills/interview/SKILL.md)
5. 근거와 완료 기준이 있는 P0를 최대 3개로 좁히고 비목표·입출력·오류·픽스처·슬라이스 검증을 정한다. 모듈 하나면 계약은 SPEC 8절에 둔다. S0는 입력 하나가 실행부터 출력까지 지나가는 뼈대다. [SPEC 절차](harness/.agents/skills/spec/SKILL.md)
6. 같은 DB를 쓰는 검증은 서로 영향을 줄 수 있어 순차 실행한다. 병렬로 하려면 DB·포트·생성물 등 검증 자원까지 분리하고 쓰기 범위가 겹치지 않아야 한다. [병렬 분할](harness/.agents/skills/delegate/tmux.md)
7. 보고 도착은 작업자의 주장이다. 모든 보고 회수·작업자 정지 → 변경 범위 확인 → 루트의 슬라이스 검증·회귀 확인 → 공유 문서 갱신·DONE 판정 순서다. [회수와 검증](harness/.agents/skills/delegate/tmux.md)
8. 기존 staged 내용은 유지하고 이번 구현·검증 결과를 기록한다. 자동 스테이징·커밋은 보류하고 사유를 알린다. 임의 reset·stash나 다른 파일까지 포함한 커밋을 하지 않는다. [Git 절차](harness/.agents/skills/delegate/git-workflow.md)
9. 실제 코드·테스트를 근거로 KNOWLEDGE와 현재 출제 내용을 갱신한다. 이미 푼 회차의 문제·답·점수는 보존하고 변경 사실과 새 회차·개정 위치를 연결한다. [학습 이력](harness/.agents/skills/interview/learning.md)
10. S0의 검증 통과와 현재 작동하는 경로만 완료로 설명한다. 저장 스텁은 P0 미완료이며 통합 검증 통과나 제출 준비 완료와 같지 않다. 이를 RETRO·전체 정리·문항에 그대로 반영한다. [마무리 검증](harness/.agents/skills/wrapup/SKILL.md)
11. `4/16문항 · 6/8점 · 미응답 12문항`으로 남긴다. 출제를 멈추고 문제·해설·재개 위치와 답한 범위의 약점·복습 행동을 안내한다. 미응답을 오답으로 채점하거나 제출을 미루지 않는다. [채점 기준](harness/.agents/skills/interview/learning.md)
12. 검사한 설치·보존·텍스트 전달·상태 조회 동작과 과거 실행의 기록은 확인할 수 있다. 실제 모델의 전체 구현·퀴즈 진행과 현재 비용은 별도 리허설이 필요하고, 평가 규칙은 당일 안내로 확인한다. [검증 범위](#설계와-검증), [당일 확인 목록](docs/01-cofa-probe.md)

</details>

다 풀었다면 **과제 설치부터 마무리까지의 흐름, 내가 판단할 지점, 완료를 증명할 근거**를 문서를 덮고 1분 동안 설명해 보세요. 막히는 주제는 해설의 복습 위치로 돌아가면 됩니다.
