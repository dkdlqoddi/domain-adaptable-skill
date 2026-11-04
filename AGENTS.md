# 저장소 유지보수 지침

이 저장소는 해커톤 과제에 설치하는 Claude 원본과 Codex 호환 설치를 제공하는 하네스의 원본이다. 이 저장소 자체가 해커톤 과제는 아니다.

- 배포할 지침은 `harness/CLAUDE.md`, 스킬은 `harness/.claude/skills/<name>/SKILL.md`에서 관리한다.
- `harness/` 아래의 지침·템플릿은 설치 대상 프로젝트의 작업 절차다. 유지보수 중 이 저장소에 과제용 SPEC·TASKS를 만들지 않는다.
- 설치는 `scripts/install.sh <과제 디렉터리>`이며 기본 도구는 Claude다. 대회용 Codex는 `--tool codex`로 설치한다.
- Python 3.8 이상과 표준 라이브러리를 유지한다. 새 런타임 의존성을 추가하지 않는다.
- 기존 파일 충돌은 쓰기 전에 중단하고, `--force`는 백업 후 교체한다. 기존 `docs/` 내용은 항상 보존한다.
- 다섯 스킬의 사용자 호출 전용 정책(`disable-model-invocation: true`, Codex 설치의 `agents/openai.yaml`)을 유지한다. 스킬 참조와 모듈 지침 이름 변경 시 설치기·검사·사용 문서를 함께 갱신한다.
- `codex` 브랜치와 함께 고칠 때는 각 브랜치에서 같은 도구로 설치한 결과가 같은지 비교한다. 변환은 Markdown에만 적용되므로 하네스 Markdown에서 두 지침 파일 이름을 한 문장에 함께 쓰지 않는다.
- 모델 이름도 변환 대상이다(`gpt-6.1-sol`·`gpt-6-sol` → `opus`, `gpt-6-luna`·`gpt-5.6-terra` → `sonnet`; 원본은 실행기의 `TIERS`). Codex는 대회 허용 모델 네 개만 쓰고, 같은 별칭의 역변환은 등급표의 tier로 구분한다. 하네스 Markdown에 두 도구의 모델 이름을 함께 쓰지 않는다.
- 검증: `bash scripts/check.sh`. 배포 변경 시 `bash scripts/pack.sh`로 `dist/harness.zip`도 생성한다. `dist/`는 커밋하지 않는다.
- `examples/`의 과거 대화·비용·코드·커밋 기록은 당시 실행의 증거다. Codex 실행 결과로 바꾸어 적지 않는다. 현재 사용법은 README와 치트시트에 둔다.
- 기존 미커밋 변경을 보존하고, 작업한 파일만 검토해 커밋한다.
