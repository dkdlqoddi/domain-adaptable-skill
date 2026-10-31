#!/usr/bin/env python3
"""브리프 텍스트를 tmux 안의 codex --yolo 초기 프롬프트로 전달한다."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def run_worker(run_dir):
    metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    prompt = (run_dir / "prompt.txt").read_text(encoding="utf-8")
    try:
        result = subprocess.run(
            [metadata["codex"], "--yolo", "--no-alt-screen", "-C", metadata["project"], prompt],
            cwd=metadata["project"], check=False)
        code, error = result.returncode, ""
    except OSError as exc:
        code, error = 127, str(exc)
    (run_dir / "exit.json").write_text(
        json.dumps({"exit_code": code, "error": error}), encoding="utf-8")
    return code


def start(args):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", args.id):
        raise ValueError("ID는 영문·숫자로 시작하는 64자 이하 영문·숫자·_-만 가능합니다")
    executables = {name: shutil.which(name) for name in ("git", "tmux", "codex")}
    for name, path in executables.items():
        if not path:
            raise ValueError("실행 파일이 없습니다: " + name)
    project = args.project.resolve(strict=True)
    top = subprocess.run([executables["git"], "-C", str(project), "rev-parse", "--show-toplevel"],
                         check=True, text=True, capture_output=True).stdout.strip()
    if project != Path(top).resolve():
        raise ValueError("--project에는 Git 프로젝트 루트를 지정하세요")
    subprocess.run([executables["git"], "-C", str(project), "rev-parse", "--verify", "HEAD"],
                   check=True, capture_output=True)
    paths = [args.brief] + args.instruction
    materials = []
    for path in paths:
        path = path if path.is_absolute() else project / path
        contents = path.read_text(encoding="utf-8")
        if not contents.strip():
            raise ValueError("빈 브리프·지침은 전달하지 않습니다: " + str(path))
        materials.append((path, contents))
    session = "harness-" + hashlib.sha256(str(project).encode()).hexdigest()[:12] + "-" + args.id
    exists = subprocess.run([executables["tmux"], "has-session", "-t", "=" + session],
                            capture_output=True)
    if exists.returncode == 0:
        raise ValueError("이미 실행 중인 세션입니다: " + session + " (보고와 종료 상태를 먼저 확인)")
    git_path = subprocess.run(
        [executables["git"], "-C", str(project), "rev-parse", "--git-path", "harness-runs"],
        check=True, text=True, capture_output=True).stdout.strip()
    runs = Path(git_path)
    if not runs.is_absolute():
        runs = project / runs
    runs.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix=args.id + "-", dir=str(runs))).resolve()
    report = run_dir / "report.md"
    prompt = (
        "당신은 위임된 슬라이스의 구현 담당이다. 아래 브리프와 지침 전문을 읽고 작업하라.\n"
        "다른 작업자가 같은 프로젝트에서 병렬 작업 중이다. 브리프의 쓰기 범위만 수정하라.\n"
        "공유 docs, 계약, Git 인덱스는 루트 담당이다. 스테이징·커밋·브랜치 전환·되돌리기 금지.\n"
        "추가 위임 없이 직접 수행하라. 계약 변경이 필요하면 BLOCKER를 보고하고 멈춰라.\n"
        "검증 결과, 변경 파일, 핵심 알고리즘·복잡도·경계 사례·근거 위치, 한계를 보고하라.\n"
        "작업의 마지막에만 아래 보고 파일을 작성하라(이 파일만 쓰기 범위 예외).\n"
        "첫 줄은 STATUS: COMPLETE 또는 STATUS: BLOCKED. COMPLETE는 지정 검증 통과 시에만.\n"
        "report.tmp에 전체 내용을 쓴 뒤 report.md로 이름을 바꿔 완성본을 게시하라.\n"
        "보고 게시 뒤에는 어떤 파일도 수정하지 말고 대기하라. 최종 검증·DONE 판정은 루트가 한다.\n"
        "보고 파일: " + str(report) + "\n\n")
    for path, contents in materials:
        prompt += "--- 자료: " + str(path) + " ---\n" + contents + "\n\n"
    metadata = {"id": args.id, "project": str(project), "session": session,
                "run_dir": str(run_dir), "report": str(report), "codex": executables["codex"]}
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    (run_dir / "run.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    # tmux의 다중 인자 실행을 사용한다. 프롬프트를 셸 코드나 키 입력으로 해석하지 않는다.
    try:
        subprocess.run([executables["tmux"], "new-session", "-d", "-s", session,
                        "-c", str(project), sys.executable, str(Path(__file__).resolve()),
                        "_worker", str(run_dir)], check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        (run_dir / "exit.json").write_text(
            json.dumps({"exit_code": exc.returncode, "error": exc.stderr}), encoding="utf-8")
        raise
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    launch = commands.add_parser("start", help="독립 슬라이스의 Codex 세션 시작")
    launch.add_argument("--project", type=Path, default=Path.cwd())
    launch.add_argument("--id", required=True)
    launch.add_argument("--brief", type=Path, required=True)
    launch.add_argument("--instruction", type=Path, action="append", default=[],
                        help="전문으로 전달할 루트·모듈 지침 (반복 가능)")
    worker = commands.add_parser("_worker", help=argparse.SUPPRESS)
    worker.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    try:
        return run_worker(args.run_dir) if args.command == "_worker" else start(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print("위임 시작 실패: " + str(exc), file=sys.stderr)
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            print(exc.stderr.decode() if isinstance(exc.stderr, bytes) else exc.stderr, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
