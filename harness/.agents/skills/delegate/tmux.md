# tmux에서 Codex에 텍스트 위임

독립 슬라이스는 이 절차로 동시에 실행한다. Python 3.8+ 표준 라이브러리와 `git`, `tmux`, 로그인된 `codex`가 필요하다.
`--yolo`는 승인·샌드박스를 끈다. 사용자가 허용한 작업 환경에서만 실행하며, 상위 실행 제한이 있으면 순차 구현한다.
내장 서브에이전트 도구 유무와 무관하게 사용할 수 있다. 루트의 도구·보안 설정을 변경하지 않는다.

## 분할과 시작
1. 의존성이 모두 DONE인 TODO를 고른다. S0는 먼저 끝낸다. 쓰기 파일, 잠금 파일, 생성물, 테스트 DB·포트까지 겹치지 않아야 한다. 겹치면 순차 실행한다.
2. 기본 동시 실행은 2개, 독립 범위가 분명하면 최대 3개. 각 브리프에 실제 쓰기 파일·검증·기존 변경과 관련 지침을 적는다. `docs/`와 Git 변경은 루트만 한다.
3. 아래 명령을 슬라이스마다 실행한다. 루트 지침과 해당 모듈 지침을 `--instruction`으로 전달한다. 하위 폴더에 적용되는 추가 지침이 있으면 함께 전달한다.

```bash
python3 .agents/skills/delegate/scripts/tmux_codex.py start \
  --project "$PWD" --id S1 --brief docs/briefs/S1.md \
  --instruction AGENTS.md --instruction api/AGENTS.md
python3 .agents/skills/delegate/scripts/tmux_codex.py start \
  --project "$PWD" --id S2 --brief docs/briefs/S2.md \
  --instruction AGENTS.md --instruction ui/AGENTS.md
```

모듈이 하나면 없는 모듈 지침 인자는 뺀다. 실제 루트 지침이 다른 위치라면 그 파일을 지정한다.
[scripts/tmux_codex.py](scripts/tmux_codex.py)는 브리프·지침 **전문**을 읽어 `codex --yolo --no-alt-screen -C <프로젝트> <텍스트>`의 단일 인자로 전달한다.
셸 치환이나 `eval`을 쓰지 않아 `$`, 따옴표, 백틱, 여러 줄을 그대로 보존한다. 초기 TUI 준비를 추측하는 고정 sleep도 쓰지 않는다.
반환 JSON의 `session`, `run_dir`, `report`를 TASKS 담당 칸에 적고 DOING으로 바꾼다. 실행 자료는 Git 내부 `harness-runs/`에 있어 커밋 대상이 아니다.

## 관찰과 회수
- 루트는 실행 중인 범위를 건드리지 않고 별도 읽기·검토·자료 정리를 진행한다. 공유 파일을 쓰는 테스트와 통합 검증은 작업자들이 멈춘 뒤 실행한다.
- `tmux capture-pane -p -S -100 -t '=세션명'`으로 진행·오류를 확인하거나 `tmux attach-session -t '=세션명'`으로 연결한다. 같은 출력만 계속 조회하지 않는다.
- 완료 조건은 `report` 파일의 `STATUS: COMPLETE` 또는 `STATUS: BLOCKED`와 전체 보고다. 프롬프트 복귀·무출력·세션 종료만으로 성공 처리하지 않는다. 보고에는 검증 실제 출력과 변경 파일이 있어야 한다.
- 세션이 끝났는데 보고가 없으면 `run_dir/exit.json`과 변경 파일을 확인하고 BLOCKED로 남긴다. 인증·제한·실행 오류는 보고하고 원인을 해결한 뒤 재실행한다. 무한 재시도하지 않는다.
- 모든 작업자의 완성된 보고를 읽고 각 세션을 `tmux kill-session -t '=세션명'`으로 종료한다. 다른 세션·서버를 종료하지 않는다. 이어 루트에서 변경 범위 확인 → 슬라이스 검증·회귀 → 공유 문서 갱신 → 개별 커밋한다.
- BLOCKED도 반드시 회수한다. 계약 변경은 루트만 하며, 같은 계약을 쓰는 작업자들이 멈춘 뒤 수정한다. 검증 실패·범위 이탈은 숨기지 않는다.
- 중단해야 하면 해당 세션만 종료하고 현재 변경을 보존한다. 보고 없는 변경은 검토 전까지 미완료다. 모든 관련 작업자가 멈춘 뒤 같은 브리프로 루트에서 이어갈 수 있다.

`tmux`·Codex가 없거나 실행이 허용되지 않으면 사유를 알리고 같은 브리프로 순차 수행한다. 이 실행기는 범위 충돌을 자동 판정하지 않으므로 시작 전 분할은 루트 책임이다.
