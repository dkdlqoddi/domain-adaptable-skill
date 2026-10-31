#!/usr/bin/env python3
"""표준 라이브러리만 사용하는 하네스 설치·호환 형식 변환기."""
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
SKILLS = SOURCE / ".claude/skills"
COMMANDS = ("kickoff", "interview", "spec", "delegate", "wrapup")


def codex_text(text):
    """Claude 전용 표기와 지침 파일명을 Codex 형식으로 바꾼다."""
    if text.startswith("---\n"):
        _, frontmatter, body = text.split("---\n", 2)
        fields = [line for line in frontmatter.splitlines()
                  if not line.startswith(("disable-model-invocation:", "argument-hint:"))]
        text = "---\n" + "\n".join(fields) + "\n---\n" + body
    for name in COMMANDS:
        text = re.sub(r"/" + name + r"\b(?!/)", lambda _: "$" + name, text)
    return (text.replace(".claude/skills/", ".agents/skills/")
            .replace("CLAUDE.md", "AGENTS.md")
            .replace("module-claude.template.md", "module-agents.template.md")
            .replace("/clear", "/new")
            .replace("/스킬명", "$스킬명")
            .replace("$ARGUMENTS", "호출 메시지의 인자")
            .replace("Agent 도구(general-purpose)", "사용 가능한 서브에이전트 도구"))


def command_text(text, source):
    """commands/ 본문의 링크는 모델이 프로젝트 루트 기준으로 열므로 루트 기준 skills/ 경로로 바꾼다."""
    def relocate(match):
        label, link = match.groups()
        if "://" in link or link.startswith(("/", "#")):
            return match.group(0)
        target = Path(os.path.relpath((source.parent / link).resolve(), SOURCE)).as_posix()
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
        if not source.is_file():
            continue
        relative = source.relative_to(SKILLS)
        text = source.read_text(encoding="utf-8")
        if tool == "codex":
            text = codex_text(text).replace(
                "${CLAUDE_SKILL_DIR}", ".agents/skills/" + relative.parts[0])
            if relative.name == "module-claude.template.md":
                relative = relative.with_name("module-agents.template.md")
        files.append((prefix / relative, text.encode(), False))
        if source.name == "SKILL.md":
            name = source.parent.name
            if tool == "codex":
                policy = b"policy:\n  allow_implicit_invocation: false\n"
                files.append((prefix / name / "agents/openai.yaml", policy, False))
            elif tool == "claude-commands":
                command = command_text(text, source)
                files.append((Path(".claude/commands") / (name + ".md"), command.encode(), False))
    rules = (SOURCE / "CLAUDE.md").read_text(encoding="utf-8")
    if tool == "codex":
        rules = codex_text(rules)
    data = rules.encode()
    files.append((rule_path(destination, tool, data), data, False))
    templates = SKILLS / "kickoff/templates/docs"
    for source in sorted(templates.rglob("*.md")):
        text = source.read_text(encoding="utf-8")
        if tool == "codex":
            text = codex_text(text)
        files.append((Path("docs") / source.relative_to(templates), text.encode(), True))
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
    command = "codex → $kickoff" if tool == "codex" else "claude → /kickoff"
    print("다음: 첫 커밋 뒤 " + command + " README.md <마감 시각, 예: 13:00>")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="이미 존재하는 과제 프로젝트 디렉터리")
    parser.add_argument("--tool", choices=("claude", "claude-commands", "codex"), default="claude")
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
