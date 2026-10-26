"""리허설 2 산출물을 examples/ 폴더 모양으로 모은다. 사용: python3 assemble.py <rehearsal2 폴더> <출력 폴더>"""
import glob
import json
import os
import shutil
import sys

R, OUT = sys.argv[1], sys.argv[2]
RESUME = "(같은 세션에 이어서 답함)"
PROMPTS = {
    "01-kickoff": "/kickoff",
    "02-interview-q1": "/interview",
    "04-interview-d1": "/interview digest <03의 답변>",
    "05-interview-q2": "/interview",
    "07-interview-d2": "/interview digest <06의 답변>",
    "08-interview-d2-reply": "용어 분리에 동의합니다. GLOSSARY에 넣어 주세요. 그리고 실제 에러 줄과 폴더 모양은 과제에 들어 있는 samples/(지난밤과 그 전날 밤 로그)에서 직접 확인할 수 있으니, 그걸 보고 담당자에게 물을 질문을 줄여 주세요. " + RESUME,
    "10-interview-d3": "/interview digest (앞 단계 판단: '실패 로그' 정의를 추천대로 바꾸는 데 동의) 담당자 답변: <09의 답변>",
    "12-interview-d4": "/interview digest (앞 단계 판단: 추천대로 담당자 기준을 따르고 그 줄을 고친다. 소스 줄 번호 제안은 /spec에서) ⑤ 가설 확인에 대한 담당자 답변: <11의 답변>",
    "13-decide": "/decide 지난 결과 보관 방식: 도구가 돌 때마다 결과를 회귀 날짜별 텍스트 파일로 남기고, 앞선 날짜 중 가장 최근 결과와 비교한다. (…) 채널 글 붙여 넣기는 기각.",
    "14-decide-reply": "AI가 /interview digest 4회차에서 이 보관 방식을 추천했고, 사람이 그대로 수용했습니다. " + RESUME,
    "15-spec": "/spec",
    "16-workspace": "/workspace (앞 단계 판단: D-004의 '다른 테스트끼리는 따로 묶는다'는 추천대로 그대로 둡니다.)",
    "17-delegate-S0": "/delegate S0",
    "18-delegate-S0-go": "네, 이대로 위임하세요. " + RESUME,
    "19-delegate-S1": "/delegate S1",
    "20-delegate-S1-go": "네, 추천대로 2번 확인을 유지하고 위임하세요. " + RESUME,
    "21-lean-S1": "/lean",
    "22-lean-S1-apply": "1, 2 둘 다 승인합니다. kept_groups는 추천대로 둡니다. " + RESUME,
    "23-delegate-S2": "/delegate S2",
    "24-delegate-S2-go": "네, 이대로 위임하세요. " + RESUME,
    "26-interview-demo-digest": "/interview digest (S2까지 만든 실제 출력을 담당자에게 보여 주고 받은 반응입니다.) <25의 답변>",
    "28-interview-split-digest": "/interview digest <27의 답변>",
    "29-spec-F7": "/spec all (앞 단계 판단: 6회차 어긋남은 추천대로 (나)로 봅니다. 구현 중에 새로 나온 F7의 우선순위와 끊는 위치를 정하고, 계약이 바뀌면 갱신해 주세요.)",
    "30-workspace-S4": "/workspace generate (CONTRACT v2의 F7을 작업판에 슬라이스로 넣어 주세요.)",
    "31-delegate-S3": "/delegate S3",
    "32-delegate-S3-go": "추천대로 오류 경로에서는 보관 폴더를 만들지 않습니다. 이대로 위임하세요. " + RESUME,
    "33-verify-all": "/verify all",
    "34-delegate-S4": "/delegate S4",
    "35-delegate-S4-go": "네, 이대로 위임하세요. " + RESUME,
    "36-lean-all": "/lean all",
    "37-lean-all-apply": "1·2 예, 3 유지. " + RESUME,
    "38-wrapup": "/wrapup all",
}


def persona_questions():
    """페르소나 세션 기록에서 사람이 보낸 질문을 순서대로 꺼낸다."""
    files = glob.glob(os.path.expanduser("~/.claude/projects/*persona-home/*.jsonl"))
    qs = []
    for line in open(max(files, key=os.path.getsize)):
        d = json.loads(line)
        m = d.get("message") or {}
        if d.get("type") == "user" and isinstance(m.get("content"), str):
            qs.append(m["content"])
    return qs


os.makedirs(os.path.join(OUT, "transcripts"), exist_ok=True)
qs = persona_questions()
pi = 0
for path in sorted(glob.glob(os.path.join(R, "runs", "[0-9][0-9]-*.md"))):
    name = os.path.basename(path)[:-3]
    body = open(path).read().rstrip() + "\n"
    if "persona" in name:
        head = "> 사람이 담당자(페르소나 AI)에게 보낸 말\n\n" + "\n".join("> " + l for l in qs[pi].splitlines()) + "\n\n## 담당자 답변\n\n"
        pi += 1
    else:
        head = "> 입력: `%s`\n\n" % PROMPTS[name].replace("`", "'")
    open(os.path.join(OUT, "transcripts", name + ".md"), "w").write(head + body)

P = os.path.join(R, "project")
for d in ("docs", "fixtures", "samples"):
    shutil.copytree(os.path.join(P, d), os.path.join(OUT, d), dirs_exist_ok=True)
for f in ("regsum.py", "test_regsum.py"):
    shutil.copy(os.path.join(P, f), OUT)
os.makedirs(os.path.join(OUT, "task"), exist_ok=True)
shutil.copy(os.path.join(P, "README.md"), os.path.join(OUT, "task", "README.md"))
if os.path.exists(os.path.join(P, ".gitignore")):
    shutil.copy(os.path.join(P, ".gitignore"), os.path.join(OUT, "gitignore.txt"))
os.makedirs(os.path.join(OUT, "kit"), exist_ok=True)
for f in ("persona.md", "task-README.md", "make_samples.py", "run.sh", "persona.sh", "clean-env.sh", "settings.json", "summarize.py", "assemble.py"):
    shutil.copy(os.path.join(R, "kit", f), os.path.join(OUT, "kit", f))
print("transcripts:", len(glob.glob(os.path.join(OUT, "transcripts", "*.md"))), "persona 질문:", pi, "/", len(qs))
