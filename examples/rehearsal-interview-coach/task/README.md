# 과제: 인터뷰 연습 도우미

저희 팀 코치들이 선수들과 인터뷰 연습을 하는데, 매번 수기로 하다 보니 힘듭니다.
선수가 답변하면 피드백을 줄 수 있는 도구가 있으면 좋겠어요.
자세한 내용은 담당자(우측 채팅)에게 물어보세요.

제출: 저장소와 실행 방법.

## 실행 방법 (설치 → 실행 → 확인)
1. **설치**: Python 3.10 이상만 있으면 된다. 패키지 설치 없음(표준 라이브러리만). Windows는 아래 `python3`를 `python`으로.
2. **실행**: `python3 api/server.py` — 기록 파일은 기본 `data/records.json`(없으면 빈 상태로 시작, 첫 저장 때 생성).
   샘플 기록으로 보려면: `cp fixtures/records.sample.json /tmp/records.json && python3 api/server.py --data /tmp/records.json`
3. **확인**: 브라우저에서 http://localhost:8765 → "선수" 목록에 김민수·박지훈·이서준이 보인다. 종료는 Ctrl+C.
   자동 테스트: `python3 -m unittest discover -s api -p 'test_*.py'` → `OK`

현재 상태(2026-10-23 리허설): S0 뼈대(서버·선수 목록)까지 완료. 비교 화면·저장은 `docs/TASKS.md`의 S1~S4, 복기는 `docs/RETRO.md`.
