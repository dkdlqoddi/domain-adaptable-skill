---
name: wrapup
description: 제출 전 통합 검증·정리·실행 README와 RETRO를 작성한다. 필수 지식·실제 알고리즘 문서와 16문항 심화 퀴즈·해설로 사후 Q&A를 준비한다. 퀴즈는 건너뛸 수 있다.
disable-model-invocation: true
argument-hint: "[check | retro] — 없으면 check → retro → 퀴즈"
---

# /wrapup — 마무리와 복기

사용: `/wrapup [check | retro]` — 인자가 없으면 check → retro → 퀴즈를 진행한다.

## 왜
평가는 결과물만이 아니라 사후 Q&A(상위권은 면접)에서 "내가 만든 것을 내가 이해하고 있는가"를 본다.
마감 직전에 처음 합치면 반드시 터진다. 한 번 더 전체를 돌려 보고, 문서에서 복기 자료를 뽑아 머릿속에 다시 넣는 것이 마지막 시간의 가장 높은 투자수익이다.
새 기능은 이 시점부터 금지다.

## 흐름
- 파일을 바꾸기 전에 [../delegate/git-workflow.md](../delegate/git-workflow.md)의 시작 상태를 확인한다.
- 인자가 없으면 check → retro → 퀴즈를 이어서 한다. check에서 사람에게 물을 것(삭제 후보·화면 확인)은 한 메시지로 묻고, 답을 받은 뒤 retro로 간다.
- check 뒤에도 검증 실패가 남아 있으면 retro 전에 하나만 묻는다: 고친 뒤 `/wrapup` 재실행 / 실패를 RETRO 4절에 `검증 실패: <명령> — <증상>`으로 적고 진행. 추천은 TASKS 시간 계획의 남은 시간으로 정한다(마감이 가까우면 진행).
- `check`를 주면 check만 한다.
- `retro`를 단독으로 주면 먼저 check 1번의 통합 검증을 다시 실행한다. 실패가 남으면 위와 같이 묻는다. 같은 호출에서 check를 통과했다면 중복 실행하지 않는다.

## check
1. **통합 검증**: SPEC의 P0와 TASKS를 대조해 미완료 항목을 먼저 명시한다. DONE 슬라이스 검증 명령을 모두 실행 → 진입점을 1회 기동해 첫 화면·첫 명령 응답 확인 → 모듈이 여럿이면 경계마다 CONTRACT 샘플로 1회 왕복. 실패하면 재현 먼저(`/delegate` 6번과 같은 순서). 결과를 TASKS 통합 체크포인트에 한 줄. 테스트 통과와 P0 전체 완료를 구분한다.
2. **화면이 있으면**: 빌드·린트로 컴파일 에러 확인. 사람에게 첫 화면·핵심 흐름·빈 상태·에러 상태를 **직접** 확인 요청. 세션에 브라우저 자동화 도구가 있으면 같은 시나리오를 돌려 콘솔 에러를 센다. 저장소에 테스트 의존성을 추가하지는 않는다.
3. **실행 README**: 프로젝트 README에 **설치 → 실행 → 확인** 3단계가 있는지. 없으면 10줄 이내로 만든다. 평가자가 그대로 따라 할 수 있어야 한다.
4. **저장소 전체 정리**:
   - `git ls-files`로 파일 목록만 보고 미사용 파일·모듈, 구현 하나뿐인 추상화, 설정만 있고 안 쓰는 것, 샘플·데모 코드 잔재를 찾는다.
   - `grep -rn "TODO\|FIXME\|console.log\|print(\|lorem\|placeholder\|shortcut:" --exclude-dir={node_modules,.git,dist} -I`로 표식을 모은다.
   - `git status --short`로 추적되지 않는 잔재(`__pycache__`, 빌드 산출물, 임시 파일)도 본다.
   - 기존 미커밋 작업은 보존한다. 삭제 후보는 묶어서 한 번 승인 → 지운 것은 결정으로 기록 → 코드가 바뀌면 관련 검증 재실행. `shortcut:` 주석은 retro 7절로 넘긴다.
5. **커밋**: [../delegate/git-workflow.md](../delegate/git-workflow.md)에 따라 검토한 변경 파일만 `"wrapup: <한 줄>"`로 커밋한다. 기존 staged 변경이 있으면 자동 커밋은 보류한다.

## retro → `docs/RETRO.md`
읽기: `docs/SPEC.md`, `docs/DECISIONS.md`, `docs/TASKS.md`, `docs/GLOSSARY.md`, (있으면) `docs/CONTRACT.md`의 모듈 표와 `docs/KNOWLEDGE.md`. 핵심 알고리즘의 실제 함수·호출부·테스트를 필요한 만큼 확인한다.
[../interview/learning.md](../interview/learning.md)에 따라 KNOWLEDGE의 필수 지식·알고리즘·복잡도·대안·한계를 실제 코드와 맞추고, **16문항**과 별도 해설을 QUIZ·QUIZ-ANSWERS에 작성한다. 구현되지 않은 P0·실패한 검증은 그대로 명시한다.
형식 고정:

```
# RETRO
## 1. 무엇을 만들었나 (3문장)
## 2. 사용자와 핵심 흐름 (GLOSSARY 용어로)
## 3. 구조 (모듈 표 + 왜 이렇게 나눴나 / 안 나눴나)
## 4. SPEC 대비 (P0 완료·미완료, P1, 비목표로 뺀 것과 이유)
## 5. 핵심 결정 (5개 이내: 선택·대안·이유 — DECISIONS 요약)
## 6. 거절하거나 축소한 AI 제안 (목록과 이유)
## 7. 알고 쓴 지름길과 한계 (shortcut 목록, 바꿀 조건)
## 8. 시간이 더 있다면 (우선순위 3개)
## 9. 필수 지식과 심화 문답 (KNOWLEDGE·QUIZ·QUIZ-ANSWERS 참조, 알고리즘·한계·검증의 핵심 요약)
```
끝나면 같은 Git 절차로 `docs/RETRO.md`, `docs/KNOWLEDGE.md`, `docs/QUIZ.md`, `docs/QUIZ-ANSWERS.md`와 이번 검증으로 바뀐 TASKS만 검토해 `"retro"`로 커밋한다. 보류 시 사유를 알린다.

## 퀴즈 (retro 작성 뒤, 커밋 보류와 무관)
[../interview/grill.md](../interview/grill.md)의 요약 → 작성한 16문항을 4문항씩 → 채점을 진행한다(위에서 확인한 자료와 만든 문서는 재작업하지 않는다). 사람이 "그만"이면 남은 문제는 문서에 두고 중단한다. 제출·푸시와는 무관하다.
채점으로 바뀐 QUIZ·QUIZ-ANSWERS는 같은 Git 절차로 별도 검토·커밋하거나 보류 사유를 남긴다. 점수나 미완료 때문에 기존 제출을 지연하지 않는다.

## 출력 (메시지마다 15줄 이내)
- check: 검증·화면·README·정리 결과를 한 줄씩. 삭제 후보가 있으면 묶어서 한 번 묻는다.
- retro: `RETRO.md 커밋: <해시 또는 보류 사유>` 한 줄 → 이어서 퀴즈.
- 끝(채점 뒤) 마지막 줄: "RETRO.md와 KNOWLEDGE.md를 읽고, 약점은 QUIZ-ANSWERS.md의 근거 코드·테스트로 확인하세요."
