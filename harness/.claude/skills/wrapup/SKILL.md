---
name: wrapup
description: 제출 전 마무리. 최종 검증과 잔재 정리(check), 그리고 사후 Q&A·면접 대비용 복기 문서 docs/RETRO.md 생성(retro). 종료 60분 전 check, 30분 전 retro.
disable-model-invocation: true
argument-hint: "[check | retro | all(기본)]"
---

# /wrapup — 마무리와 복기

## 왜
평가는 결과물만이 아니라 사후 Q&A(상위권은 면접)에서 "내가 만든 것을 내가 이해하고 있는가"를 본다.
문서에서 복기 자료를 뽑고 그것을 읽으며 머릿속에 다시 넣는 것이 마지막 30분의 가장 높은 투자수익이다.
새 기능은 이 시점부터 금지다.

## check (마감 60분 전)
1. `/verify all`에 해당하는 검증을 실행한다. 이미 했으면 결과를 재사용한다.
2. 프로젝트 README에 **설치 → 실행 → 확인** 3단계가 있는지. 없으면 10줄 이내로 만든다. 평가자가 그대로 따라 할 수 있어야 한다.
3. 잔재 후보 찾기(삭제는 묶어서 한 번 승인):
   `grep -rn "TODO\|FIXME\|console.log\|print(\|lorem\|placeholder" --exclude-dir={node_modules,.git,dist} -I`
   데모용 더미 문구, 디버그 출력, 주석 처리된 코드, 미사용 파일.
4. `shortcut:` 주석을 모아 retro 7절에 넘긴다.
5. UI가 있으면 사용자에게: 내장 브라우저에서 첫 화면·핵심 흐름·빈 상태·에러 상태를 **직접** 확인 요청.

## retro (마감 30분 전) → `docs/RETRO.md`
읽기: `docs/SPEC.md`, `docs/DECISIONS.md`, `docs/TASKS.md`, `docs/GLOSSARY.md`, `docs/CONTRACT.md`의 모듈 표. 코드는 진입점 1개 외에 열지 않는다.
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

## 출력
변경 요약 → 마지막 줄: "RETRO.md를 처음부터 끝까지 읽어보세요. 설명 못 하는 항목이 있으면 지금 그 코드를 열어 확인하세요."
