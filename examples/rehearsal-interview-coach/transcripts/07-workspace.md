`/workspace all` 완료. 모듈 2개(`api/`, `ui/`)의 지침, 슬라이스 보드, 결정 2건을 만들고 감사까지 통과해 커밋했습니다 (`26503a8`).

**1. analyze: 구조**

신규 프로젝트라 `docs/CONTRACT.md`의 모듈 표를 그대로 폴더로 만들었습니다. 폴더 이름 `api`·`ui`는 GLOSSARY 용어가 아니라 CONTRACT v2가 이미 확정한 이름을 따랐습니다 (가정).

| 폴더 | 아키타입 | 쓰기 | 읽기 전용 | 열지 않음 | 실행 명령 | 검증 명령 |
|---|---|---|---|---|---|---|
| `api/` | C 컨트롤러(+파일 저장) | `api/**` | CONTRACT A·B·C·D, SPEC P0·5절, `fixtures/*.json` | `ui/**`, `data/` | `python3 api/server.py --data /tmp/records.json` | `python3 -m unittest discover -s api -p 'test_*.py'` |
| `ui/` | D 인터페이스 | `ui/**` | CONTRACT A·B, SPEC F1·F2·4·5절, `fixtures/*.response.json`, GLOSSARY | `api/**` | 같은 서버 → localhost:8765 | 브라우저 시나리오(SPEC F2·F1 완료 기준) |

**2. generate: 만든 것**

- `api/CLAUDE.md`, `ui/CLAUDE.md`: 각 22줄. 범위·명령·아키타입 규칙 한 줄만.
- `docs/TASKS.md`: 검증 약어(`UP`/`TEST`/`SMOKE`), S0 뼈대 + P0 슬라이스 S1~S4 + P1 S5. 순서는 S0 → (S1‖S2) → (S3‖S4) → S5.
- `docs/DECISIONS.md`: D-007 (ui의 Mock은 S0 서버의 스텁 응답, 별도 mock 파일·분기 없음), D-008 (ui 검증은 브라우저 시나리오, Playwright 의존성 추가 안 함).
- 픽스처는 8개가 이미 있어 새로 만들지 않았고, `records.sample.json`에서 players·compare 두 응답과 PUT 응답이 계산으로 나오는지 스크립트로 확인했습니다 (모두 일치).

**리허설 가정 (사람 확인 필요)**

- S0은 뼈대라서 `api/`·`ui/` 두 폴더를 한 에이전트가 순차로 씁니다. 이후 슬라이스는 한 폴더씩.
- S0의 compare·PUT은 선수 이름으로 픽스처를 골라 돌려주는 스텁입니다. S1·S3에서 교체.
- ui 슬라이스의 실제 서버 연결 확인은 api 슬라이스 DONE 뒤 통합 체크포인트에서 루트가 Playwright로 합니다.

**3. audit 결과**

- [x] 두 모듈의 쓰기 범위가 겹치지 않는다 (`api/**` / `ui/**`)
- [x] 모듈 CLAUDE.md가 가리키는 경로 11개 모두 존재
- [x] 모든 슬라이스에 검증 명령이 있고 실행된다 (TEST는 0건 OK, SMOKE·curl은 `server.py` 미구현으로만 실패, 포트 8765 비어 있음)
- [x] 모듈 CLAUDE.md 22줄·22줄 ≤ 40, 루트 44줄 ≤ 80
- [x] S0 있음
- [x] 모듈 수 2 ≤ 4

추가하지 않은 것: 공유 모듈(E), Makefile·스크립트 파일, mock 전용 파일, 브라우저 테스트 의존성, P2 슬라이스.
확인하지 못한 것·리스크: 2단계 마감(20:51)이 임박해 S0는 바로 위임해야 합니다. 병렬 위임 시 `docs/TASKS.md` 같은 표의 인접 행 수정이 머지 충돌을 낼 수 있어 루트가 해소해야 합니다.

다음: `/delegate S0`
