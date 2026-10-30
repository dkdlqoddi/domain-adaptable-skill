# 리허설 3 키트 — 처음 보는 반도체 과제 (직접 하는 리허설용)

2차 예선(4시간) 전에 **사람이 직접** 5개 명령을 돌려 보는 키트입니다. 과제는 반도체 팹 현장 과제이고, 담당자 역할은 다른 AI 채팅이 맡습니다.

> ⚠️ **`persona.md`와 `after-rehearsal/` 폴더는 리허설이 끝날 때까지 열지 마세요.** 숨은 사실과 정답이 들어 있습니다. `samples/`는 과제 데이터라 열어 봐도 됩니다.

## 준비 (10분)
명령은 새 터미널에 입력합니다. 첫 줄의 `R`은 이 저장소 경로이고, 터미널을 새로 열면 그 줄부터 다시 입력합니다.
1. 새 폴더에 과제를 놓고 하네스를 설치한 뒤 첫 커밋을 합니다. 첫 커밋이 있어야 이후 커밋과 `/delegate`가 보는 diff에 내 작업만 남습니다.
   ```
   R=~/013_hackathon/domain-adaptable-skill
   mkdir -p ~/r3 && cd ~/r3 && git init
   cp "$R/examples/rehearsal-3-yield-kit/task-README.md" README.md
   cp -r "$R/examples/rehearsal-3-yield-kit/samples" .
   bash "$R/scripts/install.sh" "$PWD"
   git status --short
   git add -- README.md samples/ CLAUDE.md .claude/ docs/
   git diff --cached --stat
   git commit -qm "과제 초기 상태 + 하네스"
   ```
   위 초기 커밋은 **새로 만든 리허설 폴더의 명시된 초기 자료만** 포함합니다. 기존 `~/r3`가 있다면 새 폴더 이름을 사용하세요. Codex는 설치에 `--tool codex`를 붙이고 커밋 목록의 `CLAUDE.md .claude/`를 `AGENTS.md .agents/`로 바꿉니다. 이후 슬라이스 커밋은 파일별로 합니다.
2. 페르소나를 준비합니다. 아래 명령은 `persona.md`를 화면에 띄우지 않고 한글이 깨지지 않게 클립보드로 복사합니다(WSL 기준. macOS는 `pbcopy < $R/examples/rehearsal-3-yield-kit/persona.md`).
   ```
   powershell.exe -NoProfile -Command "Get-Content -Raw -Encoding UTF8 '$(wslpath -w $R/examples/rehearsal-3-yield-kit/persona.md)' | Set-Clipboard"
   ```
   Gemini 같은 다른 AI의 **새 채팅**에 붙여 넣고 보냅니다. 답이 "네, 준비됐습니다. 편하게 물어보세요." 한 줄이면 준비가 끝난 것입니다. 지시문을 요약하는 답이 나오면 읽지 말고 그 채팅을 닫은 뒤 새 채팅에서 다시 합니다.
3. Claude를 개인 플러그인·MCP·자동 메모리를 끈 채로 시작합니다. 그냥 `claude`로 열면 이것들이 함께 켜져 실전 환경과 달라집니다. 설정 파일은 리허설 2 키트의 것을 씁니다.
   ```
   claude --strict-mcp-config --settings $R/examples/rehearsal-2-regress-triage/kit/settings.json
   ```

## 진행 (2시간 압축판, 실전은 `/kickoff 4h`)
- 준비 3에서 연 Claude에 `/kickoff 2h` → 이후는 각 명령의 `다음:` 안내를 따릅니다. `docs/03-cheatsheet.md`의 표를 옆에 둡니다. Codex는 `codex`로 시작해 `$kickoff 2h`, 슬라이스 뒤에는 `/new`를 씁니다.
- 명령은 5개입니다: `/kickoff` → `/interview` → `/spec` → `/delegate` → `/wrapup`. 인터뷰가 끝나면 `/interview`가 이어서 다지기·요약·퀴즈를 합니다.
- `/interview`가 만든 질문을 본인 말로 바꿔 페르소나 채팅에 묻고, 받은 답을 통째로 `/interview <답변>`에 붙입니다. 정리하고 다음 질문까지 한 번에 나옵니다.
- `/delegate`는 위임 → 검증 → 과잉 설계 정리 → 커밋까지 합니다. 슬라이스 하나가 끝나면 `/clear`.
- 슬라이스 두 개쯤 끝나면 실제 출력을 페르소나에게 한 번 보여 주고 반응을 받습니다.
- 마무리 단계(2시간이면 1:35부터)에 `/wrapup` 한 번 → 퀴즈까지 풀고 `RETRO.md`를 끝까지 읽습니다.

## 연습할 것
- 명령 순서가 손에 붙는가, 판단 요청에 바로 답할 수 있는가
- 샘플 데이터를 먼저 보고, 이상한 점을 질문으로 바꾸는가
- 다지기 질문에 추천만 고르지 않고 내 말로 답할 수 있는가
- `/delegate`가 내놓는 제거 후보를 보고 바로 고르는가(고른 것은 `DECISIONS.md`에 자동 기록)
- 슬라이스마다 `/clear` 하는가

## 끝난 뒤
`after-rehearsal/answer-key.md`를 열어 숨은 사실과 함정을 확인하고, 내 SPEC·결정·결과와 비교합니다. 정답 계산은 `python3 $R/examples/rehearsal-3-yield-kit/after-rehearsal/check_answer.py ~/r3/samples/2026-10-25`입니다.
