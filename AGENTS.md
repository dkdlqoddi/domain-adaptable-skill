# 저장소 유지보수 지침

이 저장소는 해커톤 과제에 설치하는 Codex 하네스의 원본이다. 이 저장소 자체가 해커톤 과제는 아니다.

- 배포할 지침은 `harness/AGENTS.md`, 스킬은 `harness/.agents/skills/<name>/SKILL.md`에서 관리한다.
- `harness/` 아래의 지침·템플릿은 설치 대상 프로젝트의 작업 절차다. 유지보수 중 이 저장소에 과제용 SPEC·TASKS를 만들지 않는다.
- 설치는 `scripts/install.sh <과제 디렉터리>`이며 기본 도구는 Codex다. Claude 호환 형식은 `scripts/install.py`가 생성한다.
- Python 3.8 이상과 표준 라이브러리를 유지한다. 새 런타임 의존성을 추가하지 않는다.
- 기존 파일 충돌은 쓰기 전에 중단하고, `--force`는 백업 후 교체한다. 기존 `docs/` 내용은 항상 보존한다.
- 다섯 스킬의 사용자 호출 전용 정책(`agents/openai.yaml`)을 유지한다. 스킬 참조와 모듈 지침 이름 변경 시 설치기·검사·사용 문서를 함께 갱신한다.
- 검증: `bash scripts/check.sh`. 배포 변경 시 `bash scripts/pack.sh`로 `dist/harness.zip`도 생성한다. `dist/`는 커밋하지 않는다.
- `examples/`의 과거 대화·비용·코드·커밋 기록은 당시 실행의 증거다. Codex 실행 결과로 바꾸어 적지 않는다. 현재 사용법은 README와 치트시트에 둔다.
- 기존 미커밋 변경을 보존하고, 작업한 파일만 검토해 커밋한다.
