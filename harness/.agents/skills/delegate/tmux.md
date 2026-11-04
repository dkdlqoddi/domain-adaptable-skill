# tmux에서 작업자에 텍스트 위임

독립 슬라이스는 이 절차로 동시에 실행한다. Python 3.8+ 표준 라이브러리와 `git`, `tmux`, 로그인된 작업자 CLI가 필요하다.
실행기는 자기가 설치된 스킬 폴더로 작업자 CLI를 고른다: Codex 설치면 비대화형 `codex exec --yolo`, Claude 설치면 `claude -p --permission-mode bypassPermissions`. 둘 다 승인·샌드박스를 끄므로 사용자가 허용한 작업 환경에서만 실행한다. 루트의 도구·보안 설정을 변경하지 않는다.
모델 선택은 [routing.md](routing.md). 기본 `--tier implement`는 `gpt-6.1-sol` medium, `reason`은 같은 모델 high, `light`는 기계적 수정·추출용 `gpt-6-luna` medium이다. `fallback`·`legacy`는 검증된 대체용. `--effort`로 추론을 조절하며 `--model`만 바꾸면 tier의 effort는 유지된다. `--worker codex|claude`는 작업자 CLI를 고른다. Codex는 허용된 네 모델만 실행한다.

## 분할과 시작
1. 의존성이 모두 DONE인 TODO를 고른다. S0는 먼저 끝낸다. 쓰기 파일, 잠금 파일, 생성물, 테스트 DB·포트까지 겹치지 않아야 한다. 겹치면 순차 실행한다.
2. 기본은 1개, `--parallel`이면 독립 작업 2개, 시간상 이득이 분명하면 최대 6개. 실행기도 프로젝트당 6개까지 허용하며, 동시 시작 요청은 잠금으로 직렬화한다. 보고 없이 끝나 원인 확인용으로 남은 세션도 종료 전까지 포함한다. 각 브리프에 쓰기 파일·검증·기존 변경·지침을 적는다. `docs/`와 Git 변경은 루트만 한다.
3. 아래 명령을 슬라이스마다 실행한다. 루트 지침은 실행기가 처리한다: 작업자 CLI가 스스로 읽는 루트 지침은 다시 넣지 않고, 읽지 않는 쪽의 루트 지침은 자동으로 함께 전달한다. 모듈 지침만 `--instruction`으로 넘긴다(모듈이 하나면 생략).

```bash
python3 .agents/skills/delegate/scripts/tmux_codex.py start \
  --project "$PWD" --id S1 --brief docs/briefs/S1.md --instruction api/AGENTS.md
python3 .agents/skills/delegate/scripts/tmux_codex.py start \
  --project "$PWD" --id S2 --brief docs/briefs/S2.md --tier light
```

[scripts/tmux_codex.py](scripts/tmux_codex.py)는 브리프·지침 **전문**을 읽어 작업자 CLI의 단일 프롬프트 인자로 전달한다(작업 디렉터리는 프로젝트 루트). 처음 보는 폴더의 신뢰 확인이나 사용자 입력에서 멈추지 않고, 보고를 마치면 스스로 끝난다.
셸 치환이나 `eval`을 쓰지 않아 `$`, 따옴표, 백틱, 여러 줄을 그대로 보존한다. 작업자에게는 사용자 입력을 기다리지 말고 질문은 BLOCKED 보고로 하라고 지시한다.
반환 JSON의 `session`, `run_dir`, `progress`, `report`, `model`, `effort`를 TASKS 담당 칸에 적고 DOING으로 바꾼다. `instructions`는 실제로 전달한 지침 목록이다. 실행 자료는 Git 내부 `harness-runs/`에 있어 커밋 대상이 아니다. `prompt_bytes`는 전달 문맥의 바이트 수다. Codex의 긴 출력은 `events.jsonl`, 완료 턴 토큰은 `usage.json`에 남고 부모는 짧은 보고만 읽는다.

## 샌드박스에서 막힐 때
루트가 샌드박스 안에서 돌면 `.git`이 읽기 전용이고 tmux 소켓 접속도 막힌다(`Read-only file system`, `Operation not permitted`). 실행기가 이를 알리면 같은 명령을 샌드박스 밖(권한 상승)으로 다시 요청한다. 거절되면 사용 가능한 서브에이전트 도구로, 그것도 없으면 루트에서 순차 구현한다.

## 부모의 진행 상황 조회
```bash
python3 .agents/skills/delegate/scripts/tmux_codex.py wait --project "$PWD" --timeout 60
```
- 셸 `sleep`으로 주기를 맞추지 않는다. `wait`는 작업의 상태가 바뀌거나(보고 도착·실패·보고 없는 종료) 작업이 `blocked` 단계에 들어가거나, 실행 중인 작업이 없거나, `--timeout`초(기본 60)가 지나면 돌아온다. 단계·메시지 갱신으로는 깨지 않아 작업자가 많아도 자주 깨지 않는다. 도구의 명령 제한 시간은 그보다 길게 둔다. 돌아올 때마다 바뀐 점만 사용자에게 요약하고(보고가 왔으면 `<ID>: <구현된 처리 한 줄>`, 시간 초과면 작업별 현재 단계를 한 줄로), 실행 중인 작업이 남았으면 다시 `wait`한다. 그사이 독립적인 읽기·검토를 해도 된다.
- JSON의 `changed`는 상태가 바뀌었거나 `blocked`에 들어간 작업, `running`은 아직 실행 중인 작업, `timed_out`은 그런 일 없이 시간이 다 된 경우다. `runs`에는 슬라이스별 최신 실행의 `state`, `session_present`, `model`, `effort`, `usage`, `progress`(단계·메시지·UTC 갱신 시각), `progress_age_seconds`, `exit`, 보고 경로가 있다. `--id S1 --id S2`로 범위를 좁힌다.
- 터미널 출력은 기본으로 싣지 않는다. 진행이 오래 멈췄거나 `FAILED`·`STOPPED`이면 그 작업만 `status --id S1 --tail 40`으로 본다(최대 200줄).
- 작업자는 초기 프롬프트의 `progress --run-dir ... --phase implementing --message '현재 상황'` 명령으로 시작·구현·검증·차단 때 갱신한다. 단계는 `planning`, `implementing`, `verifying`, `blocked`. 긴 작업은 가능한 도구 호출 사이에 약 60초마다 갱신한다. 이 갱신은 `wait`를 깨우지 않고 시간 초과 때 `runs`의 `progress`로 보인다(`blocked` 진입만 바로 깨운다).
- `progress_age_seconds`는 마지막 보고 이후 시간이며 프로세스 생존 신호가 아니다. `session_present`는 세션 존재 여부이며 완료 근거가 아니다. 무응답만으로 완료·실패를 추정하지 않는다.
- `RUNNING`은 보고 전 실행 중, `REPORTED_COMPLETE`·`REPORTED_BLOCKED`는 작업자 보고 도착, `FAILED`는 CLI 비정상 종료, `STOPPED`는 보고 없이 종료된 실행이다. `INVALID_REPORT`·`UNREADABLE`·`errors`·`output_error`도 확인한다. 보고 도착은 루트의 검증·DONE 판정을 대신하지 않는다.

## 관찰과 회수
- 루트는 실행 중인 범위를 건드리지 않고 별도 읽기·검토·자료 정리를 진행한다. 공유 파일을 쓰는 테스트와 통합 검증은 작업자들이 멈춘 뒤 실행한다.
- 더 긴 출력은 `tmux capture-pane -p -S -100 -t '=세션명:'`으로 확인하거나 `tmux attach-session -t '=세션명'`으로 연결한다. 같은 출력만 계속 조회하지 않는다.
- 완료 조건은 `report` 파일의 `STATUS: COMPLETE` 또는 `STATUS: BLOCKED`와 전체 보고다. 프롬프트 복귀·무출력·세션 종료만으로 성공 처리하지 않는다. 보고에는 검증 명령·종료 코드·핵심 출력과 변경 파일이 있어야 한다. 긴 로그는 파일 경로로 남긴다.
- 보고 없이 끝난 작업(`FAILED`·`STOPPED`)은 실행기가 화면을 10분 남긴다. `status --tail`로 원인(로그인·제한·네트워크 등)을 읽고, `run_dir/exit.json`과 변경 파일을 확인해 BLOCKED로 남긴다. 원인을 해결한 뒤 재실행하며 무한 재시도하지 않는다.
- 작업자가 보고 대신 질문으로 끝났으면(`STOPPED`) 브리프를 보강해 다시 시작하거나 루트에서 이어간다.
- 작업자는 보고를 마치면 스스로 끝난다. 모든 보고를 읽은 뒤 남은 세션(원인 확인용·멈춘 작업)만 `tmux kill-session -t '=세션명'`으로 종료한다. 다른 세션·서버를 종료하지 않는다. 이어 루트에서 변경 범위 확인 → 슬라이스 검증·회귀 → 공유 문서 갱신 → 개별 커밋한다.
- BLOCKED도 반드시 회수한다. 계약 변경은 루트만 하며, 같은 계약을 쓰는 작업자들이 멈춘 뒤 수정한다. 검증 실패·범위 이탈은 숨기지 않는다.
- 중단해야 하면 해당 세션만 종료하고 현재 변경을 보존한다. 보고 없는 변경은 검토 전까지 미완료다. 모든 관련 작업자가 멈춘 뒤 같은 브리프로 루트에서 이어갈 수 있다.

`tmux`·작업자 CLI가 없거나 실행이 허용되지 않으면 사유를 알리고 사용 가능한 서브에이전트 도구에 같은 브리프를 전달한다(모델·effort는 routing에서 선택한 값, 전체 대화는 복사하지 않는다. 모든 보고를 받은 뒤 처리). 그것도 없으면 같은 브리프로 순차 수행한다. 이 실행기는 범위 충돌을 자동 판정하지 않으므로 시작 전 분할은 루트 책임이다.

토큰 집계: `python3 .agents/skills/delegate/scripts/tmux_codex.py usage --project "$PWD"` (`--id S1`로 모든 재시도 포함). 관측된 완료 턴만 합산하므로 `unknown_runs`·`errors`도 확인한다. 캐시 입력은 입력에 포함된다. 루트 세션과 다른 CLI 사용량은 별도다.
