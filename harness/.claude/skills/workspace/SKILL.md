---
name: workspace
description: 디렉토리 구조를 분석하거나 신규 설계해 모듈별 CLAUDE.md를 만들고, TASKS.md를 수직 슬라이스로 채운 뒤, 경로·쓰기 범위·검증 명령을 감사한다. CONTRACT 확정 후 1회 실행.
disable-model-invocation: true
argument-hint: "[analyze | generate | audit | all(기본)]"
---

# /workspace — 모듈 경계와 작업판

## 왜
세션마다 자기 폴더와 계약서만 읽게 하면 토큰이 크게 줄고 후반까지 정확도가 유지된다.
그러려면 폴더별로 **쓰기 범위 · 읽기 전용 · 열지 않음**이 적힌 짧은 지침이 필요하다.
단, 모듈 분할 자체가 과잉 설계가 될 수 있다. 작은 과제는 모듈 1~2개가 정상이다.

## 1. analyze — 구조 파악
- `find . -maxdepth 2 -type d -not -path '*/node_modules*' -not -path '*/.git*' -not -path '*/dist*'`. 파일 내용은 열지 않는다. 실행·테스트 명령을 알기 위한 설정 파일 1~2개(package.json, pyproject.toml, Makefile)만 예외.
- 각 폴더를 아키타입 A~E로 분류한다. 기준과 예시: [archetypes.md](archetypes.md)
- 신규 프로젝트면 `docs/CONTRACT.md`의 모듈 표를 그대로 폴더로 만든다. 폴더 이름은 `GLOSSARY.md` 용어를 쓴다.
- 출력 표: | 폴더 | 아키타입 | 쓰기 | 읽기 전용 | 열지 않음 | 실행 명령 | 검증 명령 |

## 2. generate — 지침과 작업판
- 모듈마다 `<모듈>/CLAUDE.md`를 [module-claude.template.md](module-claude.template.md)로 만든다. **40줄 이하.** 프로젝트별 값(명령·경로·아키타입 규칙 한 줄)만 채우고 설명을 늘리지 않는다. 모듈이 하나뿐이면 만들지 않는다(루트 CLAUDE.md로 충분).
- `fixtures/`에 CONTRACT의 샘플 입출력 파일이 없으면 만든다.
- `docs/TASKS.md` 슬라이스 채우기:
  - **S0 = 걸어다니는 뼈대.** 실행되고 입력 하나가 모든 모듈을 지나 출력까지 간다(내용은 하드코딩이어도 됨). 항상 첫 번째.
  - P0 기능 하나당 슬라이스 1~2개. 각 행에 쓰기 범위 폴더와 검증 명령을 **반드시** 적는다.
  - P1은 TODO로 뒤에. P2는 적지 않는다.
  - 검증 명령은 가장 싼 것: 테스트 1개, curl 1줄, 픽스처 입력→출력 diff.
  - **표의 한 칸은 2문장 이하.** 세부 기준은 SPEC의 F# 행과 CONTRACT 절을 가리킨다. 보드는 매 세션 시작마다 읽히므로 짧아야 한다.

## 3. audit — 감사 (generate 직후 반드시)
어긋나면 고친다:
- [ ] 두 모듈의 쓰기 범위가 겹치지 않는다
- [ ] 모든 `<모듈>/CLAUDE.md`가 가리키는 경로(`docs/CONTRACT.md`, `fixtures/...`)가 실제로 있다
- [ ] 모든 슬라이스에 검증 명령이 있고, 명령 자체는 실행된다(미구현이라 실패하는 것은 OK, 명령이 틀린 것은 수정)
- [ ] 각 모듈 CLAUDE.md ≤ 40줄, 루트 CLAUDE.md ≤ 80줄
- [ ] S0가 있다
- [ ] 모듈 수 ≤ 4. 넘으면 합칠 것을 먼저 제안한다

## 출력
감사 결과 체크리스트 → 마지막 줄: "다음: `/delegate <첫 TODO 슬라이스>`"(처음이면 S0).
