"""모델 호출 없이 실제 tmux와 가짜 Codex로 텍스트 전달·격리·실패를 검증한다."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
RUNNER = next((ROOT / "harness").glob(".*/skills/delegate/scripts/tmux_codex.py"))
TMUX = shutil.which("tmux")


class WorkerTest(unittest.TestCase):
    def test_worker_keeps_prompt_literal_and_records_cli_failure(self):
        spec = importlib.util.spec_from_file_location("tmux_codex", RUNNER)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            prompt = "여러 줄\n$HOME $(touch bad) `touch bad` ' \"\n"
            (path / "prompt.txt").write_text(prompt, encoding="utf-8")
            (path / "run.json").write_text(json.dumps({"codex": "/fake/codex", "project": directory}))
            with mock.patch.object(runner.subprocess, "run", return_value=mock.Mock(returncode=7)) as call:
                self.assertEqual(runner.run_worker(path), 7)
            self.assertEqual(call.call_args[0][0],
                             ["/fake/codex", "--yolo", "--no-alt-screen", "-C", directory, prompt])
            self.assertNotIn("shell", call.call_args[1])
            self.assertEqual(json.loads((path / "exit.json").read_text())["exit_code"], 7)
            self.assertFalse((path / "report.md").exists())


@unittest.skipUnless(TMUX, "tmux가 없어 실제 tmux 통합 검사 생략 (가짜 Codex 사용)")
class TmuxTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="harness-tmux-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.project = self.base / "과제 ' $name `literal`"
        self.project.mkdir()
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        subprocess.run(["git", "-C", str(self.project), "-c", "user.name=Test",
                        "-c", "user.email=test@example.com", "-c", "commit.gpgsign=false",
                        "commit", "-qm", "init", "--allow-empty"], check=True)
        binaries = self.base / "bin"
        binaries.mkdir()
        self.socket = str(self.base / "tmux.sock")
        self.addCleanup(lambda: subprocess.run([TMUX, "-S", self.socket, "kill-server"],
                                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        tmux = binaries / "tmux"
        tmux.write_text("#!" + sys.executable + "\nimport os, sys\nos.execv(" + repr(TMUX) +
                        ", [" + repr(TMUX) + ", '-S', " + repr(self.socket) + "] + sys.argv[1:])\n")
        tmux.chmod(0o755)
        codex = binaries / "codex"
        codex.write_text("#!" + sys.executable + '''
import json, os, pathlib, sys, time
prompt = sys.argv[-1]
report = pathlib.Path(next(line.split(": ", 1)[1] for line in prompt.splitlines()
                           if line.startswith("보고 파일: ")))
(report.parent / "argv.json").write_text(json.dumps({"args": sys.argv[1:], "cwd": os.getcwd()}))
if "FAIL_CLI" in prompt:
    sys.exit(9)
report.write_text("STATUS: COMPLETE\\n검증: fake only\\n")
deadline = time.monotonic() + 15
while not (report.parent / "release").exists() and time.monotonic() < deadline:
    time.sleep(0.02)
''', encoding="utf-8")
        codex.chmod(0o755)
        self.env = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ["PATH"])
        self.instructions = "루트 규칙 ' $literal\n공유 파일 수정 금지\n"
        (self.project / "rules.md").write_text(self.instructions, encoding="utf-8")

    def launch(self, identity, text="작업", expected=0):
        brief = self.project / (identity + ".md")
        brief.write_text(text, encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", str(RUNNER), "start", "--project", str(self.project),
                                 "--id", identity, "--brief", brief.name, "--instruction", "rules.md"],
                                env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout) if expected == 0 else result

    def wait_file(self, path):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if path.exists():
                return
            time.sleep(0.02)
        self.fail("파일 생성 대기 초과: " + str(path))

    def test_two_sessions_pass_full_text_and_protect_existing_session(self):
        payload = "한글\n$HOME $(touch SHOULD_NOT_EXIST) `touch SHOULD_NOT_EXIST` ' \"\n"
        first = self.launch("S1", payload)
        second = self.launch("S2", "독립 작업\n")
        self.assertNotEqual(first["session"], second["session"])
        for run, body in ((first, payload), (second, "독립 작업\n")):
            report = Path(run["report"])
            self.wait_file(report)
            captured = json.loads((report.parent / "argv.json").read_text())
            self.assertEqual(captured["cwd"], str(self.project))
            self.assertEqual(captured["args"][:4], ["--yolo", "--no-alt-screen", "-C", str(self.project)])
            self.assertIn(body, captured["args"][4])
            self.assertIn(self.instructions, captured["args"][4])
            self.assertEqual(captured["args"][4], (report.parent / "prompt.txt").read_text())
        runs = self.project / ".git/harness-runs"
        before = sorted(runs.iterdir())
        self.assertIn("이미 실행 중", self.launch("S1", expected=1).stderr)
        self.assertEqual(sorted(runs.iterdir()), before)
        self.assertFalse((self.project / "SHOULD_NOT_EXIST").exists())
        staged = subprocess.run(["git", "-C", str(self.project), "diff", "--cached", "--name-only"],
                                text=True, capture_output=True, check=True)
        self.assertEqual(staged.stdout, "")
        for run in (first, second):
            directory = Path(run["run_dir"])
            (directory / "release").touch()
            self.wait_file(directory / "exit.json")
            self.assertEqual(json.loads((directory / "exit.json").read_text())["exit_code"], 0)

    def test_cli_failure_does_not_create_success_report(self):
        run = self.launch("S3", "FAIL_CLI")
        directory = Path(run["run_dir"])
        self.wait_file(directory / "exit.json")
        self.assertEqual(json.loads((directory / "exit.json").read_text())["exit_code"], 9)
        self.assertFalse(Path(run["report"]).exists())

    def test_missing_material_fails_before_creating_run(self):
        (self.project / "rules.md").unlink()
        self.launch("S4", expected=1)
        self.assertFalse((self.project / ".git/harness-runs").exists())


if __name__ == "__main__":
    unittest.main()
