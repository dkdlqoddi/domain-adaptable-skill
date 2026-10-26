# 리허설 키트

| 파일 | 쓰임 |
|---|---|
| `task-README.md` | 과제 지시문 원본(다섯 줄). 직접 리허설할 때 빈 폴더에 `README.md`로 둔다 |
| `make_samples.py` | 가짜 회귀 로그 15개를 만든다: `python3 make_samples.py samples` |
| `persona.md` | 담당자 역할 지시문. 다른 AI 채팅의 첫 메시지로 붙여 넣는다. **직접 리허설할 사람은 읽지 말 것**(숨은 사실이 있음) |
| `run.sh`, `persona.sh`, `clean-env.sh`, `settings.json` | 자동 리허설에 쓴 실행 스크립트. 폴더 모양 `kit/`·`project/`·`runs/`·`persona-home/`을 가정한다. 플러그인·동기화 스킬·MCP·자동 메모리를 끄고 명령마다 새 세션으로 돌린다 |
| `summarize.py` | `runs/*.json`에서 세션별 시간·비용·토큰 표를 만든다(`../costs.md`) |
| `assemble.py` | 산출물을 이 예시 폴더 모양으로 모은다 |
