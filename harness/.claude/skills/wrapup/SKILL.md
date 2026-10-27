---
name: wrapup
description: 제출 전 마무리. 통합 검증·저장소 전체 정리·실행 README(check), 그리고 사후 Q&A·면접 대비용 복기 문서 docs/RETRO.md 생성(retro). 종료 60분 전 check, 30분 전 retro.
disable-model-invocation: true
argument-hint: "[check | retro | all(기본)]"
---

# /wrapup — 마무리와 복기

## 왜
평가는 결과물만이 아니라 사후 Q&A(상위권은 면접)에서 "내가 만든 것을 내가 이해하고 있는가"를 본다.
마감 직전에 처음 합치면 반드시 터진다. 한 번 더 전체를 돌려 보고, 문서에서 복기 자료를 뽑아 머릿속에 다시 넣는 것이 마지막 시간의 가장 높은 투자수익이다.
새 기능은 이 시점부터 금지다.

## check (마감 60분 전)
1. **통합 검증**: `docs/TASKS.md`의 DONE 슬라이스 검증 명령을 모두 실행 → 진입점을 1회 기동해 첫 화면·첫 명령 응답 확인 → 모듈이 여럿이면 경계마다 CONTRACT 샘플로 1회 왕복. 실패하면 재현 먼저(`/delegate` 6번과 같은 순서). 결과를 TASKS 통합 체크포인트에 한 줄.
2. **화면이 있으면**: 빌드·린트로 컴파일 에러 확인. 사람에게 첫 화면·핵심 흐름·빈 상태·에러 상태를 **직접** 확인 요청. 세션에 브라우저 자동화 도구가 있으면 같은 시나리오를 돌려 콘솔 에러를 센다. 저장소에 테스트 의존성을 추가하지는 않는다.
3. **실행 README**: 프로젝트 README에 **설치 → 실행 → 확인** 3단계가 있는지. 없으면 10줄 이내로 만든다. 평가자가 그대로 따라 할 수 있어야 한다.
4. **저장소 전체 정리**:
   - `git ls-files`로 파일 목록만 보고 미사용 파일·모듈, 구현 하나뿐인 추상화, 설정만 있고 안 쓰는 것, 샘플·데모 코드 잔재를 찾는다.
   - `grep -rn "TODO\|FIXME\|console.log\|print(\|lorem\|placeholder\|shortcut:" --exclude-dir={node_modules,.git,dist} -I`로 표식을 모은다.
   - `git status --short`로 추적되지 않는 잔재(`__pycache__`, 빌드 산출물, 임시 파일)도 본다.
   - 삭제는 묶어서 한 번 승인 → 지운 것은 결정으로 기록. `shortcut:` 주석은 retro 7절로 넘긴다.
5. **커밋**: `git add <바꾼 파일> docs/ && git commit -m "wrapup: <한 줄>"`.

## retro (마감 30분 전) → `docs/RETRO.md`
읽기: `docs/SPEC.md`, `docs/DECISIONS.md`, `docs/TASKS.md`, `docs/GLOSSARY.md`, (있으면) `docs/CONTRACT.md`의 모듈 표. 코드는 진입점 1개 외에 열지 않는다.
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
## 9. 예상 질문 10개와 한 줄 답 (구조·대안·트레이드오프·검증 방법·토큰을 아낀 방법)
```
끝나면 `git add docs/RETRO.md && git commit -m "retro"`.

## 출력 (15줄 이내)
- check: 검증·화면·README·정리 결과를 한 줄씩. 삭제 후보가 있으면 묶어서 한 번 묻는다.
- retro: 마지막 줄 "RETRO.md를 처음부터 끝까지 읽어보세요. 설명 못 하는 항목이 있으면 지금 그 코드를 열어 확인하세요."
