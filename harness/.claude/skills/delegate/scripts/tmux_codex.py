#!/usr/bin/env python3
"""tmux에서 비대화형 Codex 작업자(codex exec)를 최대 6개 실행하고 부모에게 진행 상황을 제공한다."""
import argparse
from datetime import datetime, timezone
import errno
import fcntl
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time


MAX_WORKERS = 6
HOLD_SECONDS = 600  # 보고 없이 끝난 작업자 화면을 부모가 읽을 수 있게 남겨 두는 시간
CLAUDE_RULES = ("CLAUDE.md", ".claude/CLAUDE.md")  # Codex가 스스로 읽지 않는 루트 지침
SANDBOX_HINT = ("샌드박스가 .git 쓰기나 tmux 소켓을 막았을 수 있습니다. 같은 명령을 샌드박스 밖(권한 상승)으로 "
                "다시 요청하고, 거절되면 서브에이전트 도구나 루트 순차 구현으로 진행하세요.")


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def require(name):
    path = shutil.which(name)
    if not path:
        raise ValueError("실행 파일이 없습니다: " + name)
    return path


def project_paths(project):
    project = project.resolve(strict=True)
    top = subprocess.run(["git", "-C", str(project), "rev-parse", "--show-toplevel"],
                         check=True, text=True, capture_output=True).stdout.strip()
    if project != Path(top).resolve():
        raise ValueError("--project에는 Git 프로젝트 루트를 지정하세요")
    git_path = subprocess.run(["git", "-C", str(project), "rev-parse", "--git-path", "harness-runs"],
                              check=True, text=True, capture_output=True).stdout.strip()
    runs = Path(git_path)
    return project, runs if runs.is_absolute() else project / runs


def session_prefix(project):
    return "harness-" + hashlib.sha256(str(project).encode()).hexdigest()[:12] + "-"


def sessions(tmux):
    result = subprocess.run([tmux, "list-sessions", "-F", "#{session_name}"],
                            text=True, capture_output=True)
    if result.returncode:
        if any(message in result.stderr.lower() for message in
               ("no server running", "no such file or directory", "no sessions")):
            return set()
        raise subprocess.CalledProcessError(result.returncode, result.args, stderr=result.stderr)
    return set(result.stdout.splitlines())


def progress(args):
    run_dir = args.run_dir.resolve(strict=True)
    metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    if (run_dir / "report.md").exists() or (run_dir / "exit.json").exists():
        raise ValueError("보고 게시·실행 종료 뒤에는 진행 상황을 수정할 수 없습니다")
    if not args.message.strip():
        raise ValueError("진행 상황을 한 줄 이상 적어 주세요")
    update = {"phase": args.phase, "message": args.message,
              "updated_at": datetime.now(timezone.utc).isoformat()}
    write_json(run_dir / "progress.json", update)
    print(json.dumps({"id": metadata["id"], **update}, ensure_ascii=False))
    return 0


def run_status(metadata, active, tmux, tail):
    run_dir = Path(metadata["run_dir"])
    row = {key: metadata[key] for key in ("id", "session", "run_dir", "report")}
    row["session_present"] = metadata["session"] in active
    for name in ("progress", "exit"):
        path = run_dir / (name + ".json")
        row[name] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    row["progress_age_seconds"] = None
    if row["progress"]:
        updated = datetime.fromisoformat(row["progress"]["updated_at"])
        row["progress_age_seconds"] = max(0, int((datetime.now(timezone.utc) - updated).total_seconds()))
    report = Path(metadata["report"])
    report_text = report.read_text(encoding="utf-8").strip() if report.exists() else ""
    lines = report_text.splitlines()
    reported = lines[0][8:].strip() if lines and lines[0].startswith("STATUS: ") else ""
    if row["exit"] and row["exit"]["exit_code"] != 0:
        row["state"] = "FAILED"
    elif reported in ("COMPLETE", "BLOCKED") and len(lines) > 1:
        row["state"] = "REPORTED_" + reported
    elif report.exists():
        row["state"] = "INVALID_REPORT"
    elif row["exit"] or not row["session_present"]:
        row["state"] = "STOPPED"
    else:
        row["state"] = "RUNNING"
    row["output_tail"] = ""
    if tail and row["session_present"]:
        captured = subprocess.run([tmux, "capture-pane", "-p", "-J", "-S", "-" + str(tail),
                                   "-t", "=" + metadata["session"] + ":"], text=True, capture_output=True)
        row["output_tail"] = "\n".join(captured.stdout.rstrip().splitlines()[-tail:])
        if captured.returncode:
            row["output_error"] = captured.stderr.strip()
    return row


def collect(project, runs, tmux, ids, tail):
    """슬라이스별 최신 실행의 상태 목록. 실행 자료가 없으면 아무것도 만들지 않는다."""
    active = sessions(tmux)
    latest, errors = {}, []
    for path in sorted(runs.glob("*/run.json"), key=lambda item: item.stat().st_mtime_ns):
        try:
            metadata = json.loads(path.read_text(encoding="utf-8"))
            if metadata["project"] == str(project):
                latest[metadata["id"]] = metadata
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append({"path": str(path), "error": str(exc)})
    rows = []
    for identity, metadata in sorted(latest.items()):
        if ids and identity not in ids:
            continue
        try:
            rows.append(run_status(metadata, active, tmux, tail))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            rows.append({"id": identity, "run_dir": metadata.get("run_dir"),
                         "state": "UNREADABLE", "error": str(exc)})
    return active, rows, errors


def check_tail(tail):
    if not 0 <= tail <= 200:
        raise ValueError("--tail은 0~200줄이어야 합니다")


def status(args):
    check_tail(args.tail)
    project, runs = project_paths(args.project)
    active, rows, errors = collect(project, runs, require("tmux"), args.id, args.tail)
    print(json.dumps({"project": str(project), "max_workers": MAX_WORKERS,
                      "active_sessions": sorted(name for name in active if name.startswith(session_prefix(project))),
                      "runs": rows, "errors": errors}, ensure_ascii=False, indent=2))
    return 0


def signature(row):
    progress_info = row.get("progress") or {}
    exit_info = row.get("exit") or {}
    return (row.get("state"), progress_info.get("phase"), progress_info.get("message"),
            exit_info.get("exit_code"), row.get("session_present"))


def wait(args):
    """실행 중인 작업의 상태·단계·메시지가 바뀌거나, 실행 중인 작업이 없거나, 시간이 다 될 때까지 기다린다.

    셸 sleep으로 주기 조회하면 막히거나(Claude Code) 매번 전체 출력이 컨텍스트에 쌓인다.
    같은 단계·메시지의 갱신 시각만 바뀐 것은 변화로 보지 않는다.
    """
    check_tail(args.tail)
    if not 1 <= args.timeout <= 3600 or not 0 < args.interval <= 60:
        raise ValueError("--timeout은 1~3600초, --interval은 0~60초여야 합니다")
    project, runs = project_paths(args.project)
    tmux = require("tmux")
    deadline = time.monotonic() + args.timeout
    _, rows, errors = collect(project, runs, tmux, args.id, 0)
    before = {row["id"]: signature(row) for row in rows}
    changed = []
    while any(row.get("state") == "RUNNING" for row in rows) and time.monotonic() < deadline:
        time.sleep(min(args.interval, max(0.0, deadline - time.monotonic())))
        _, rows, errors = collect(project, runs, tmux, args.id, 0)
        changed = sorted(row["id"] for row in rows if before.get(row["id"]) != signature(row))
        if changed:
            break
    if args.tail:
        _, rows, errors = collect(project, runs, tmux, args.id, args.tail)
    running = [row["id"] for row in rows if row.get("state") == "RUNNING"]
    print(json.dumps({"project": str(project), "changed": changed, "running": running,
                      "timed_out": bool(running) and not changed, "runs": rows, "errors": errors},
                     ensure_ascii=False, indent=2))
    return 0


def run_worker(run_dir):
    metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    prompt = (run_dir / "prompt.txt").read_text(encoding="utf-8")
    # 대화형 TUI는 처음 보는 폴더의 신뢰 확인이나 질문에서 입력을 기다리며 멈춘다. exec는 끝나면 스스로 종료한다.
    try:
        result = subprocess.run(
            [metadata["codex"], "exec", "--yolo", "-C", metadata["project"], prompt],
            cwd=metadata["project"], stdin=subprocess.DEVNULL, check=False)
        code, error = result.returncode, ""
    except OSError as exc:
        code, error = 127, str(exc)
    write_json(run_dir / "exit.json", {"exit_code": code, "error": error})
    reported = Path(metadata.get("report", run_dir / "report.md")).exists()
    if code or not reported:
        # 세션이 바로 닫히면 로그인·네트워크 오류 화면이 사라진다. 부모가 status --tail로 읽게 남긴다.
        print("\n[harness] Codex 종료 코드 {}, 보고 {}. 원인 확인용으로 이 화면을 {}분 남깁니다.".format(
            code, "있음" if reported else "없음", HOLD_SECONDS // 60), flush=True)
        if error:
            print("[harness] " + error, flush=True)
        try:
            time.sleep(HOLD_SECONDS)
        except KeyboardInterrupt:
            pass
    return code


def read_materials(project, brief, instructions):
    """브리프와 지침 전문. Codex가 스스로 읽는 루트 AGENTS.md는 넣지 않고, 읽지 않는 Claude 지침은 자동으로 넣는다."""
    brief = brief if brief.is_absolute() else project / brief
    chosen = [brief] + [project / name for name in CLAUDE_RULES
                        if (project / name).is_file() and (project / name).read_text(encoding="utf-8").strip()]
    skipped = {(project / "AGENTS.md").resolve()}
    for path in instructions:
        path = path if path.is_absolute() else project / path
        if path.resolve() not in skipped and path.resolve() not in {item.resolve() for item in chosen}:
            chosen.append(path)
    materials = []
    for path in chosen:
        contents = path.read_text(encoding="utf-8")
        if not contents.strip():
            raise ValueError("빈 브리프·지침은 전달하지 않습니다: " + str(path))
        materials.append((path, contents))
    return materials


def start(args):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", args.id):
        raise ValueError("ID는 영문·숫자로 시작하는 64자 이하 영문·숫자·_-만 가능합니다")
    executables = {name: require(name) for name in ("git", "tmux", "codex")}
    project, runs = project_paths(args.project)
    subprocess.run([executables["git"], "-C", str(project), "rev-parse", "--verify", "HEAD"],
                   check=True, capture_output=True)
    materials = read_materials(project, args.brief, args.instruction)
    runs.mkdir(parents=True, exist_ok=True)
    # 동시에 start를 호출해도 확인과 세션 생성을 한 번에 하나씩 수행한다.
    with (runs / "start.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        prefix = session_prefix(project)
        session = prefix + args.id
        active = sessions(executables["tmux"])
        if session in active:
            raise ValueError("이미 실행 중인 세션입니다: " + session + " (보고와 종료 상태를 먼저 확인)")
        if sum(name.startswith(prefix) for name in active) >= MAX_WORKERS:
            raise ValueError("프로젝트당 최대 6개 세션입니다. 기존 작업의 보고를 회수하고 종료하세요")
        return launch(args.id, project, runs, session, executables, materials)


def launch(identity, project, runs, session, executables, materials):
    run_dir = Path(tempfile.mkdtemp(prefix=identity + "-", dir=str(runs))).resolve()
    report = run_dir / "report.md"
    progress_command = shlex.join([sys.executable, str(Path(__file__).resolve()),
                                   "progress", "--run-dir", str(run_dir)])
    prompt = (
        "당신은 위임된 슬라이스의 구현 담당이다. 아래 브리프와 지침 전문을 읽고 작업하라.\n"
        "다른 작업자가 같은 프로젝트에서 병렬 작업 중이다. 브리프의 쓰기 범위만 수정하라.\n"
        "공유 docs, 계약, 결정 기록, Git 인덱스는 루트 담당이다. 스테이징·커밋·브랜치 전환·되돌리기 금지.\n"
        "추가 위임 없이 직접 수행하라. 계약 변경이 필요하면 BLOCKER를 보고하고 멈춰라.\n"
        "사용자 입력을 기다리지 마라. 질문·승인이 필요하면 멈추고 STATUS: BLOCKED 보고의 BLOCKER: 줄에 적어라.\n"
        "검증 결과, 변경 파일, 핵심 알고리즘·복잡도·경계 사례·근거 위치, 한계를 보고하라.\n"
        "작업 시작·구현·검증·차단 시 아래 진행 명령에 --phase와 --message를 붙여 갱신하라.\n"
        "phase는 planning, implementing, verifying, blocked 중 하나, message는 현재 상황 한 줄이다.\n"
        "긴 작업도 가능한 도구 호출 사이에 약 60초마다 갱신하라. 부모가 wait·status로 확인한다.\n"
        "진행 명령: " + progress_command + "\n"
        "작업의 마지막에만 아래 보고 파일을 작성하라. 전용 진행·보고 파일은 쓰기 범위 예외다.\n"
        "첫 줄은 STATUS: COMPLETE 또는 STATUS: BLOCKED. COMPLETE는 지정 검증 통과 시에만.\n"
        "report.tmp에 전체 내용을 쓴 뒤 report.md로 이름을 바꿔 완성본을 게시하라.\n"
        "보고 게시 뒤에는 어떤 파일도 수정하지 말고 작업을 끝내라. 최종 검증·DONE 판정은 루트가 한다.\n"
        "보고 파일: " + str(report) + "\n\n")
    for path, contents in materials:
        prompt += "--- 자료: " + str(path) + " ---\n" + contents + "\n\n"
    metadata = {"id": identity, "project": str(project), "session": session,
                "run_dir": str(run_dir), "report": str(report), "codex": executables["codex"],
                "progress": str(run_dir / "progress.json")}
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    write_json(run_dir / "run.json", metadata)
    write_json(run_dir / "progress.json", {"phase": "starting", "message": "Codex 실행 준비",
                                           "updated_at": datetime.now(timezone.utc).isoformat()})
    # tmux의 다중 인자 실행을 사용한다. 프롬프트를 셸 코드나 키 입력으로 해석하지 않는다.
    try:
        subprocess.run([executables["tmux"], "new-session", "-d", "-s", session,
                        "-c", str(project), sys.executable, str(Path(__file__).resolve()),
                        "_worker", str(run_dir)], check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        write_json(run_dir / "exit.json", {"exit_code": exc.returncode, "error": exc.stderr})
        raise
    print(json.dumps({**metadata, "instructions": [str(path) for path, _ in materials[1:]]},
                     ensure_ascii=False, indent=2))
    return 0


def blocked_by_sandbox(exc, detail):
    if isinstance(exc, OSError) and exc.errno in (errno.EROFS, errno.EACCES, errno.EPERM):
        return True
    return any(text in (str(exc) + " " + detail).lower()
               for text in ("operation not permitted", "read-only file system", "permission denied"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    launch_parser = commands.add_parser("start", help="독립 슬라이스의 Codex 세션 시작")
    launch_parser.add_argument("--project", type=Path, default=Path.cwd())
    launch_parser.add_argument("--id", required=True)
    launch_parser.add_argument("--brief", type=Path, required=True)
    launch_parser.add_argument("--instruction", type=Path, action="append", default=[],
                               help="전문으로 전달할 모듈 지침 (반복 가능). 루트 지침은 자동 처리")
    inspect = commands.add_parser("status", help="부모용: 슬라이스별 최신 실행·진행·터미널 출력 JSON")
    inspect.add_argument("--project", type=Path, default=Path.cwd())
    inspect.add_argument("--id", action="append", help="조회할 슬라이스 (반복 가능, 기본 전체)")
    inspect.add_argument("--tail", type=int, default=10, help="최근 터미널 출력 줄 수 (0~200, 기본 10)")
    block = commands.add_parser("wait", help="부모용: 변화·전체 종료·시간 초과까지 기다린 뒤 상태 JSON")
    block.add_argument("--project", type=Path, default=Path.cwd())
    block.add_argument("--id", action="append", help="기다릴 슬라이스 (반복 가능, 기본 전체)")
    block.add_argument("--timeout", type=int, default=90, help="최대 대기 초 (1~3600, 기본 90)")
    block.add_argument("--interval", type=float, default=3.0, help="내부 확인 간격 초 (기본 3)")
    block.add_argument("--tail", type=int, default=0, help="돌아올 때 함께 볼 터미널 출력 줄 수 (기본 0)")
    update = commands.add_parser("progress", help="작업자용: 현재 단계·진행 상황 게시")
    update.add_argument("--run-dir", type=Path, required=True)
    update.add_argument("--phase", choices=("planning", "implementing", "verifying", "blocked"), required=True)
    update.add_argument("--message", required=True)
    worker = commands.add_parser("_worker", help=argparse.SUPPRESS)
    worker.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "_worker":
            return run_worker(args.run_dir)
        return {"start": start, "status": status, "wait": wait, "progress": progress}[args.command](args)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print("위임 명령 실패: " + str(exc), file=sys.stderr)
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) and exc.stderr else ""
        detail = detail.decode(errors="replace") if isinstance(detail, bytes) else detail
        if detail:
            print(detail, file=sys.stderr)
        if blocked_by_sandbox(exc, detail):
            print(SANDBOX_HINT, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
