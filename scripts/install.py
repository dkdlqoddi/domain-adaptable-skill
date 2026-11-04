#!/usr/bin/env python3
"""Codex 하네스 설치기. 선택적으로 Claude 호환 형식도 생성한다(표준 라이브러리)."""
import argparse
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "harness"
SKILLS = SOURCE / ".agents/skills"
COMMANDS = ("kickoff", "interview", "spec", "delegate", "wrapup")
# Claude 슬래시 메뉴의 인자 안내. Codex 원본에는 해당 필드가 없어 변환 때만 넣는다(main 원본과 같은 값).
ARGUMENT_HINTS = {
    "kickoff": "[지시문 경로 (기본 README.md)] [마감 시각 예: 13:00 | 남은 시간 예: 3h45m]",
    "interview": "[페르소나의 답변 | quiz] — 없으면 첫 질문",
    "spec": "(인자 없음)",
    "delegate": "<슬라이스 ID 또는 한 줄 설명> [--parallel | --serial]",
    "wrapup": "[check | retro] — 없으면 check → retro·전체 정리 → 퀴즈",
}
TEMPLATE_COPY = '".claude/skills/kickoff/templates/docs/."'
# 실행기 TIERS와 같은 매핑. 여러 Codex 모델이 같은 Claude 별칭을 사용할 수 있다.
MODEL_NAMES = (("gpt-6.1-sol", "opus"), ("gpt-6-sol", "opus"),
               ("gpt-5.6-terra", "sonnet"), ("gpt-6-luna", "sonnet"))


def skip_source(path):
    """실행 캐시는 배포하지 않는다(.gitignore에 가려 보이지 않아도 설치 키트에 섞일 수 있다)."""
    return "__pycache__" in path.parts or path.suffix in (".pyc", ".pyo")


def claude_text(text):
    """Codex 원본을 Claude 호환 표기·지침으로 바꾼다."""
    if text.startswith("---\n"):
        _, frontmatter, body = text.split("---\n", 2)
        name = re.search(r"^name:\s*(\S+)", frontmatter, re.M).group(1)
        hint = 'argument-hint: "' + ARGUMENT_HINTS[name] + '"\n' if name in ARGUMENT_HINTS else ""
        text = "---\n" + frontmatter + "disable-model-invocation: true\n" + hint + "---\n" + body
    for name in COMMANDS:
        text = re.sub(r"\$" + name + r"\b", lambda _: "/" + name, text)
    for codex_name, claude_name in MODEL_NAMES:
        text = re.sub(r"\b" + re.escape(codex_name) + r"\b", claude_name, text)
    return (text.replace(".agents/skills/", ".claude/skills/")
            .replace("AGENTS.md", "CLAUDE.md")
            .replace("module-agents.template.md", "module-claude.template.md")
            .replace("$스킬명", "/스킬명")
            .replace("/new", "/clear")
            .replace("사용 가능한 서브에이전트 도구", "Agent 도구(general-purpose)")
            .replace(TEMPLATE_COPY, '"${CLAUDE_SKILL_DIR}/templates/docs/."'))


def command_text(text, source):
    """commands/ 본문의 링크는 모델이 프로젝트 루트 기준으로 열므로 루트 기준 skills/ 경로로 바꾼다."""
    def relocate(match):
        label, link = match.groups()
        if "://" in link or link.startswith(("/", "#")):
            return match.group(0)
        target = claude_text(Path(os.path.relpath((source.parent / link).resolve(), SOURCE)).as_posix())
        return "[" + (target if label == link else label) + "](" + target + ")"
    return re.sub(r"\[([^\]]*)\]\(([^)]+)\)", relocate, text).replace(
        "${CLAUDE_SKILL_DIR}", ".claude/skills/" + source.parent.name)


def rule_path(destination, tool, data):
    if tool == "codex":
        return Path("AGENTS.md")
    candidates = [Path("CLAUDE.md"), Path(".claude/CLAUDE.md")]
    for relative in candidates:
        path = destination / relative
        if path.is_file() and not path.is_symlink():
            old = path.read_bytes()
            if old == data or old.startswith("# 작업 헌법 (프로젝트 루트)".encode()):
                return relative
    if not (destination / "CLAUDE.md").exists():
        return candidates[0]
    return candidates[1]


def installation_files(destination, tool):
    """(상대 경로, 내용, 기존 파일 무조건 보존 여부) 목록."""
    files = []
    prefix = Path(".agents/skills" if tool == "codex" else ".claude/skills")
    for source in sorted(SKILLS.rglob("*")):
        if not source.is_file() or skip_source(source):
            continue
        relative = source.relative_to(SKILLS)
        data = source.read_bytes()
        if tool != "codex":
            if relative.parts[-2:] == ("agents", "openai.yaml"):
                continue
            if source.suffix == ".md":
                data = claude_text(data.decode("utf-8")).encode("utf-8")
            if relative.name == "module-agents.template.md":
                relative = relative.with_name("module-claude.template.md")
        files.append((prefix / relative, data, False))
        if source.name == "SKILL.md" and tool == "claude-commands":
            command = command_text(data.decode("utf-8"), source)
            files.append((Path(".claude/commands") / (source.parent.name + ".md"),
                          command.encode("utf-8"), False))
    data = (SOURCE / "AGENTS.md").read_bytes()
    if tool != "codex":
        data = claude_text(data.decode("utf-8")).encode("utf-8")
    files.append((rule_path(destination, tool, data), data, False))
    templates = SKILLS / "kickoff/templates/docs"
    for source in sorted(templates.rglob("*.md")):
        data = source.read_bytes()
        if tool != "codex":
            data = claude_text(data.decode("utf-8")).encode("utf-8")
        files.append((Path("docs") / source.relative_to(templates), data, True))
    return files


def check_path(destination, relative):
    path = destination
    for part in relative.parts:
        path /= part
        if path.is_symlink():
            raise ValueError("심볼릭 링크 경로는 자동 변경하지 않습니다: " + str(relative))
        if path != destination / relative and path.exists() and not path.is_dir():
            raise ValueError("상위 경로가 디렉터리가 아닙니다: " + str(relative))
    if path.exists() and not path.is_file():
        raise ValueError("파일을 설치할 위치에 디렉터리가 있습니다: " + str(relative))


def install(destination, tool, force):
    pending, conflicts = [], []
    skipped = 0
    # 충돌·잘못된 경로를 전부 확인한 뒤에만 쓰기를 시작한다.
    for relative, data, preserve in installation_files(destination, tool):
        check_path(destination, relative)
        path = destination / relative
        if path.exists():
            if preserve or path.read_bytes() == data:
                skipped += 1
                continue
            conflicts.append(relative)
        pending.append((relative, data))
    if conflicts and not force:
        print("설치 중단: 기존 내용과 다른 파일이 있습니다. 아무 파일도 변경하지 않았습니다.", file=sys.stderr)
        for relative in conflicts:
            print("  충돌: " + str(relative), file=sys.stderr)
        print("기존 내용을 병합하거나, 백업 후 교체하려면 같은 명령에 --force를 붙이세요. docs/는 항상 보존합니다.", file=sys.stderr)
        return 2
    if conflicts:
        check_path(destination, Path(".harness-backups/probe"))
        backup_root = destination / ".harness-backups"
        backup_root.mkdir(exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix=datetime.now().strftime("%Y%m%d-%H%M%S-"), dir=str(backup_root)))
        for relative in conflicts:
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(destination / relative), str(saved))
        print("백업: " + str(backup) + " (자동 커밋 대상에서 제외)")
    for relative, data in pending:
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print("  설치: " + str(relative))
    print("완료: 설치 {}개, 동일 파일·기존 docs 보존 {}개 → {}".format(len(pending), skipped, destination))
    if tool != "codex" and (destination / "CLAUDE.md").exists() and (destination / ".claude/CLAUDE.md").exists():
        print("확인: CLAUDE.md와 .claude/CLAUDE.md의 규칙이 충돌하지 않는지 확인하세요.")
    command = ("codex -m gpt-6.1-sol -c 'model_reasoning_effort=\"high\"' → $kickoff"
               if tool == "codex" else "claude --model opus --effort high → /kickoff")
    print("다음: 첫 커밋 뒤 " + command + " README.md <마감 시각, 예: 13:00>")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="이미 존재하는 과제 프로젝트 디렉터리")
    parser.add_argument("--tool", choices=("codex", "claude", "claude-commands"), default="codex",
                        help="설치할 도구 (기본: codex)")
    parser.add_argument("--force", action="store_true", help="충돌 파일을 백업한 뒤 교체 (docs/는 보존)")
    args = parser.parse_args()
    destination = args.destination.resolve()
    if not destination.is_dir():
        parser.error("대상 디렉터리를 먼저 만들어 주세요")
    try:
        return install(destination, args.tool, args.force)
    except (OSError, ValueError) as exc:
        print("설치 오류: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
