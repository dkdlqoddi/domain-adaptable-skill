"""모델 호출 없이 실제 tmux와 가짜 Codex·Claude CLI로 동시 실행·등급 선택·부모 관찰·실패를 검증한다."""
import importlib.util
import io
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


def load_runner():
    spec = importlib.util.spec_from_file_location("tmux_codex", RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


class WorkerTest(unittest.TestCase):
    def run_worker(self, returncode, reported, worker="codex"):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            prompt = "여러 줄\n$HOME $(touch bad) `touch bad` ' \"\n"
            (path / "prompt.txt").write_text(prompt, encoding="utf-8")
            model, effort = runner.TIERS[worker]["light" if worker == "claude" else "implement"]
            (path / "run.json").write_text(json.dumps({
                "worker": worker, "cli": "/fake/" + worker, "model": model, "effort": effort,
                "project": directory, "report": str(path / "report.md")}))
            if reported:
                (path / "report.md").write_text("STATUS: COMPLETE\n검증 통과\n", encoding="utf-8")
            def execute(*args, **kwargs):
                if "stdout" in kwargs and reported:
                    kwargs["stdout"].write(json.dumps({"type": "turn.completed", "usage": {
                        "input_tokens": 100, "cached_input_tokens": 80, "output_tokens": 20}}) + "\n")
                return mock.Mock(returncode=returncode)
            with mock.patch.object(runner.subprocess, "run", side_effect=execute) as call, \
                    mock.patch.object(runner.time, "sleep") as hold, mock.patch("sys.stdout"):
                self.assertEqual(runner.run_worker(path), returncode)
            expected = (["/fake/claude", "-p", "--model", "sonnet", "--effort", "medium",
                         "--permission-mode", "bypassPermissions", "--output-format", "text", prompt]
                        if worker == "claude" else
                        ["/fake/codex", "exec", "--yolo", "--json", "-C", directory, "-m", "gpt-6.1-sol",
                         "-c", 'model_reasoning_effort="medium"', prompt])
            self.assertEqual(call.call_args[0][0], expected)
            self.assertEqual(call.call_args[1]["cwd"], directory)
            self.assertNotIn("shell", call.call_args[1])
            self.assertIs(call.call_args[1]["stdin"], runner.subprocess.DEVNULL)
            self.assertEqual(json.loads((path / "exit.json").read_text())["exit_code"], returncode)
            if worker == "codex":
                counts = json.loads((path / "usage.json").read_text())
                if reported:
                    self.assertEqual(counts["total_tokens"], 120)
                else:
                    self.assertIsNone(counts)
            else:
                self.assertFalse((path / "usage.json").exists())
            return runner, hold

    def test_worker_keeps_prompt_literal_and_holds_screen_after_cli_failure(self):
        runner, hold = self.run_worker(7, reported=False)
        hold.assert_called_once_with(runner.HOLD_SECONDS)

    def test_worker_with_report_and_normal_exit_closes_immediately(self):
        _, hold = self.run_worker(0, reported=True)
        hold.assert_not_called()

    def test_claude_worker_runs_headless_with_light_tier_model(self):
        _, hold = self.run_worker(0, reported=True, worker="claude")
        hold.assert_not_called()

    def test_default_worker_follows_install_path(self):
        runner = load_runner()
        self.assertEqual(runner.default_worker(), "claude" if ".claude" in RUNNER.parts else "codex")
        self.assertEqual(set(runner.TIERS), {"codex", "claude"})
        for tiers in runner.TIERS.values():
            self.assertEqual(set(tiers), {"implement", "light", "reason", "fallback", "legacy"})

    def test_competition_models_and_effort_override(self):
        runner = load_runner()
        expected = {"implement": ("gpt-6.1-sol", "medium"), "light": ("gpt-6-luna", "medium"),
                    "reason": ("gpt-6.1-sol", "high"), "fallback": ("gpt-6-sol", "medium"),
                    "legacy": ("gpt-5.6-terra", "medium")}
        for tier, (model, effort) in expected.items():
            with self.subTest(tier=tier):
                self.assertEqual(runner.model_choice("codex", tier),
                                 {"worker": "codex", "tier": tier, "model": model, "effort": effort})
        choice = runner.model_choice("codex", "fallback", "gpt-5.6-terra", "high")
        self.assertEqual((choice["model"], choice["effort"]), ("gpt-5.6-terra", "high"))
        with self.assertRaisesRegex(ValueError, "허용 모델"):
            runner.model_choice("codex", "implement", "gpt-6-astra")

    def test_usage_events_ignore_noise_and_do_not_double_count_cached_input(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            rows = [{"type": "item.completed", "usage": {"input_tokens": 999}},
                    {"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 80,
                                                         "output_tokens": 20, "reasoning_output_tokens": 5}},
                    {"type": "turn.completed", "usage": {"input_tokens": 50, "cached_input_tokens": 10,
                                                         "output_tokens": 5}}]
            invalid = [None, [], {"type": "turn.failed"}, {"type": "turn.completed", "usage": None},
                       {"type": "turn.completed", "usage": {"input_tokens": 5, "cached_input_tokens": 6,
                                                            "output_tokens": 1}},
                       {"type": "turn.completed", "usage": {"input_tokens": True, "cached_input_tokens": 0,
                                                            "output_tokens": -1}}]
            noise = "not-json\n" + "\n".join(json.dumps(row) for row in invalid) + "\n"
            path.write_text(noise + "\n".join(json.dumps(row) for row in rows) + '\n{"type":', encoding="utf-8")
            self.assertEqual(runner.summarize_events(path), {"input_tokens": 150, "cached_input_tokens": 90,
                                                            "output_tokens": 25, "total_tokens": 175, "turns": 2})
            path.write_text(noise, encoding="utf-8")
            self.assertIsNone(runner.summarize_events(path))

    def test_usage_includes_earlier_failed_attempt_and_marks_missing_counts(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            runs = project / "runs"
            for name, identity, counts in (("first", "S1", 120), ("retry", "S1", 240),
                                          ("no_usage", "S1", None), ("other", "S2", 80)):
                path = runs / name
                path.mkdir(parents=True)
                runner.write_json(path / "run.json", {"project": str(project), "id": identity,
                                                       "model": "gpt-6-luna", "effort": "medium"})
                runner.write_json(path / "exit.json", {"exit_code": 9 if name == "first" else 0})
                if counts:
                    runner.write_json(path / "usage.json", {"input_tokens": counts - 20, "output_tokens": 20,
                                                            "cached_input_tokens": 60, "total_tokens": counts})
            def collect(identity):
                output = io.StringIO()
                with mock.patch.object(runner, "project_paths", return_value=(project, runs)), \
                        mock.patch("sys.stdout", output):
                    runner.usage(mock.Mock(project=project, id=identity))
                return json.loads(output.getvalue())
            report = collect(["S1"])
            self.assertEqual(report["observed_total_tokens"], 360)
            self.assertEqual(report["unknown_runs"], 1)
            self.assertEqual(report["by_model_effort"]["gpt-6-luna/medium"]["runs"], 3)
            self.assertEqual(collect(None)["observed_total_tokens"], 440)
            (runs / "no_usage/usage.json").write_text("{broken", encoding="utf-8")
            broken = collect(["S1"])
            self.assertEqual(broken["unknown_runs"], 1)
            self.assertEqual(len(broken["errors"]), 1)
            self.assertEqual(broken["observed_total_tokens"], 360)


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
import json, os, pathlib, shlex, subprocess, sys, time
prompt = sys.argv[-1]
report = pathlib.Path(next(line.split(": ", 1)[1] for line in prompt.splitlines()
                           if line.startswith("보고 파일: ")))
progress = shlex.split(next(line.split(": ", 1)[1] for line in prompt.splitlines()
                           if line.startswith("진행 명령: ")))
(report.parent / "argv.json").write_text(json.dumps({"args": sys.argv[1:], "cwd": os.getcwd()}))
if "FAIL_CLI" in prompt:
    print("fake cli: 로그인이 필요합니다", flush=True)
    sys.exit(9)
subprocess.run(progress + ["--phase", "implementing", "--message", "샘플 구현 중"], check=True)
print("worker output: implementing", file=sys.stderr, flush=True)
(report.parent / "ready").touch()
deadline = time.monotonic() + 30
while "WAIT_REPORT" in prompt and not (report.parent / "finish").exists() and time.monotonic() < deadline:
    time.sleep(0.02)
if "NO_REPORT" in prompt:
    sys.exit(0)
blocked = "BLOCKED_REPORT" in prompt
subprocess.run(progress + ["--phase", "blocked" if blocked else "verifying",
                          "--message", "계약 확인 필요" if blocked else "검증 통과"], check=True)
temporary = report.with_suffix(".tmp")
temporary.write_text("STATUS: BLOCKED\\nBLOCKER: 계약 확인\\n" if blocked else
                     "STATUS: COMPLETE\\n검증: fake only\\n")
temporary.replace(report)
while not (report.parent / "release").exists() and time.monotonic() < deadline:
    time.sleep(0.02)
if "--json" in sys.argv:
    print(json.dumps({"type": "turn.completed", "usage": {
        "input_tokens": 100, "cached_input_tokens": 80, "output_tokens": 20}}), flush=True)
''', encoding="utf-8")
        codex.chmod(0o755)
        # 가짜 Claude CLI도 마지막 인자를 프롬프트로 읽는다. 어느 CLI가 불렸는지는 argv.json의 인자로 구분한다.
        shutil.copy2(str(codex), str(binaries / "claude"))
        self.env = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ["PATH"])
        self.instructions = "루트 규칙 ' $literal\n공유 파일 수정 금지\n"
        (self.project / "rules.md").write_text(self.instructions, encoding="utf-8")

    def launch(self, identity, text="작업", *options, expected=0):
        result = subprocess.run(self.launch_command(identity, text, *options), env=self.env,
                                text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout) if expected == 0 else result

    def launch_command(self, identity, text, *options):
        brief = self.project / (identity + ".md")
        brief.write_text(text, encoding="utf-8")
        return [sys.executable, "-B", str(RUNNER), "start", "--project", str(self.project),
                "--id", identity, "--brief", brief.name, "--instruction", "rules.md", *options]

    def command(self, *arguments, expected=0):
        result = subprocess.run([sys.executable, "-B", str(RUNNER), *arguments], env=self.env,
                                text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout) if expected == 0 else result

    def status(self, *arguments):
        return self.command("status", "--project", str(self.project), *arguments)

    def wait_file(self, path):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if path.exists():
                return
            time.sleep(0.02)
        self.fail("파일 생성 대기 초과: " + str(path))

    def test_two_sessions_pass_full_text_and_protect_existing_session(self):
        payload = "한글\n$HOME $(touch SHOULD_NOT_EXIST) `touch SHOULD_NOT_EXIST` ' \"\n"
        first = self.launch("S1", payload, "--worker", "codex")
        second = self.launch("S2", "독립 작업\n", "--worker", "codex")
        self.assertNotEqual(first["session"], second["session"])
        self.assertEqual((first["worker"], first["model"], first["effort"]), ("codex", "gpt-6.1-sol", "medium"))
        for run, body in ((first, payload), (second, "독립 작업\n")):
            report = Path(run["report"])
            self.wait_file(report)
            captured = json.loads((report.parent / "argv.json").read_text())
            self.assertEqual(captured["cwd"], str(self.project))
            self.assertEqual(captured["args"][:-1], ["exec", "--yolo", "--json", "-C", str(self.project), "-m", "gpt-6.1-sol",
                                                     "-c", 'model_reasoning_effort="medium"'])
            self.assertIn(body, captured["args"][-1])
            self.assertIn(self.instructions, captured["args"][-1])
            self.assertIn("사용자 입력을 기다리지 마라", captured["args"][-1])
            self.assertEqual(captured["args"][-1], (report.parent / "prompt.txt").read_text())
            self.assertEqual(run["prompt_bytes"], len(captured["args"][-1].encode("utf-8")))
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
        accounting = self.command("usage", "--project", str(self.project))
        self.assertEqual(accounting["observed_total_tokens"], 240)
        self.assertEqual(accounting["unknown_runs"], 0)
        self.assertEqual(self.status("--id", "S1")["runs"][0]["usage"]["total_tokens"], 120)

    def test_parent_observes_live_progress_output_and_final_report(self):
        run = self.launch("S1", "WAIT_REPORT")
        directory = Path(run["run_dir"])
        self.wait_file(directory / "ready")
        row = self.status("--id", "S1", "--tail", "20")["runs"][0]
        self.assertEqual(row["state"], "RUNNING")
        self.assertTrue(row["session_present"])
        self.assertEqual(row["progress"]["phase"], "implementing")
        self.assertEqual(row["progress"]["message"], "샘플 구현 중")
        self.assertGreaterEqual(row["progress_age_seconds"], 0)
        self.assertIn("worker output: implementing", row["output_tail"], row)
        message = "검증 중: $HOME `literal` '한글'"
        self.command("progress", "--run-dir", str(directory), "--phase", "verifying", "--message", message)
        row = self.status("--tail", "0")["runs"][0]
        self.assertEqual(row["progress"]["message"], message)
        self.assertEqual(row["output_tail"], "")
        (directory / "finish").touch()
        self.wait_file(Path(run["report"]))
        self.assertEqual(self.status()["runs"][0]["state"], "REPORTED_COMPLETE")
        before = Path(run["progress"]).read_bytes()
        self.command("progress", "--run-dir", str(directory), "--phase", "implementing",
                     "--message", "늦은 수정", expected=1)
        self.assertEqual(Path(run["progress"]).read_bytes(), before)

    def test_six_concurrent_launches_succeed_and_seventh_is_rejected(self):
        processes = [subprocess.Popen(self.launch_command("S" + str(index), "WAIT_REPORT"),
                                      env=self.env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                     for index in range(1, 8)]
        results = [(process, *process.communicate(timeout=20)) for process in processes]
        accepted = [json.loads(stdout) for process, stdout, _ in results if process.returncode == 0]
        rejected = [stderr for process, _, stderr in results if process.returncode != 0]
        self.assertEqual(len(accepted), 6, results)
        self.assertEqual(len(rejected), 1, results)
        self.assertIn("최대 6개", rejected[0])
        snapshot = self.status("--tail", "0")
        self.assertEqual(snapshot["max_workers"], 6)
        self.assertEqual(len(snapshot["active_sessions"]), 6)
        self.assertEqual(len(snapshot["runs"]), 6)
        selected = self.status("--id", accepted[0]["id"], "--id", accepted[1]["id"], "--tail", "0")
        self.assertEqual({row["id"] for row in selected["runs"]}, {run["id"] for run in accepted[:2]})

    def test_parent_sees_blocker_and_exit_without_report(self):
        blocked = self.launch("S1", "BLOCKED_REPORT")
        self.wait_file(Path(blocked["report"]))
        row = self.status("--id", "S1")["runs"][0]
        self.assertEqual(row["state"], "REPORTED_BLOCKED")
        self.assertEqual(row["progress"]["phase"], "blocked")
        stopped = self.launch("S2", "NO_REPORT")
        self.wait_file(Path(stopped["run_dir"]) / "exit.json")
        row = self.status("--id", "S2")["runs"][0]
        self.assertEqual(row["state"], "STOPPED")
        self.assertEqual(row["exit"]["exit_code"], 0)
        self.assertFalse(Path(stopped["report"]).exists())

    def test_killed_worker_and_restart_show_latest_run_only(self):
        old = self.launch("S1", "WAIT_REPORT")
        self.wait_file(Path(old["run_dir"]) / "ready")
        subprocess.run([TMUX, "-S", self.socket, "kill-session", "-t", "=" + old["session"]], check=True)
        self.assertEqual(self.status()["runs"][0]["state"], "STOPPED")
        new = self.launch("S1", "WAIT_REPORT")
        self.wait_file(Path(new["run_dir"]) / "ready")
        rows = self.status()["runs"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["run_dir"], new["run_dir"])
        self.assertEqual(rows[0]["state"], "RUNNING")
        self.assertTrue(Path(old["run_dir"]).exists())

    def test_status_before_first_launch_does_not_create_runtime_files(self):
        self.assertEqual(self.status()["runs"], [])
        self.assertFalse((self.project / ".git/harness-runs").exists())

    def test_cli_failure_keeps_error_screen_for_parent(self):
        run = self.launch("S3", "FAIL_CLI")
        directory = Path(run["run_dir"])
        self.wait_file(directory / "exit.json")
        self.assertEqual(json.loads((directory / "exit.json").read_text())["exit_code"], 9)
        self.assertFalse(Path(run["report"]).exists())
        deadline = time.monotonic() + 10
        while True:
            row = self.status("--id", "S3", "--tail", "20")["runs"][0]
            if "[harness]" in row["output_tail"] or time.monotonic() > deadline:
                break
            time.sleep(0.05)
        self.assertEqual(row["state"], "FAILED")
        self.assertEqual(row["exit"]["exit_code"], 9)
        self.assertTrue(row["session_present"])
        self.assertIn("fake cli: 로그인이 필요합니다", row["output_tail"])
        self.assertIn("종료 코드 9", row["output_tail"])

    def test_wait_returns_on_change_timeout_and_completion(self):
        run = self.launch("S1", "WAIT_REPORT")
        directory = Path(run["run_dir"])
        self.wait_file(directory / "ready")
        quick = ("wait", "--project", str(self.project), "--interval", "0.05")
        idle = self.command(*quick, "--timeout", "1")
        self.assertEqual((idle["changed"], idle["running"], idle["timed_out"]), ([], ["S1"], True))
        self.assertEqual(idle["runs"][0]["output_tail"], "")
        # 단계·메시지 갱신은 부모를 깨우지 않는다. 바뀐 내용은 시간 초과 때 runs에 보인다.
        self.command("progress", "--run-dir", str(directory), "--phase", "verifying", "--message", "검증 중")
        quiet = self.command(*quick, "--timeout", "1")
        self.assertEqual((quiet["changed"], quiet["timed_out"]), ([], True))
        self.assertEqual(quiet["runs"][0]["progress"]["message"], "검증 중")

        def wake_on(action):
            waiting = subprocess.Popen([sys.executable, "-B", str(RUNNER), *quick, "--timeout", "10"],
                                       env=self.env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(0.3)
            started = time.monotonic()
            action()
            output, error = waiting.communicate(timeout=15)
            self.assertEqual(waiting.returncode, 0, error)
            self.assertLess(time.monotonic() - started, 5)
            return json.loads(output)

        # blocked 진입은 바로 깨운다.
        blocked = wake_on(lambda: self.command("progress", "--run-dir", str(directory),
                                               "--phase", "blocked", "--message", "계약 확인 필요"))
        self.assertEqual((blocked["changed"], blocked["running"], blocked["timed_out"]), (["S1"], ["S1"], False))
        # blocked에서 벗어나는 갱신(작업자의 verifying)은 깨우지 않고, 보고 도착(상태 변화)이 깨운다.
        done = wake_on(lambda: (directory / "finish").touch())
        self.assertEqual((done["changed"], done["running"], done["timed_out"]), (["S1"], [], False))
        self.assertEqual(done["runs"][0]["state"], "REPORTED_COMPLETE")
        # 실행 중인 작업이 없으면 바로 돌아온다.
        started = time.monotonic()
        idle_done = self.command(*quick, "--timeout", "30", "--tail", "5")
        self.assertLess(time.monotonic() - started, 10)
        self.assertEqual((idle_done["changed"], idle_done["running"], idle_done["timed_out"]), ([], [], False))
        self.assertIn("worker output", idle_done["runs"][0]["output_tail"])

    def test_root_rules_are_passed_once_and_worker_own_rules_are_not_repeated(self):
        (self.project / "CLAUDE.md").write_text("클로드 루트 규칙\n", encoding="utf-8")
        (self.project / "AGENTS.md").write_text("에이전트 루트 규칙\n", encoding="utf-8")
        brief = self.project / "S5.md"
        brief.write_text("작업", encoding="utf-8")
        for worker, own, other in (("codex", "에이전트 루트 규칙", "클로드 루트 규칙"),
                                   ("claude", "클로드 루트 규칙", "에이전트 루트 규칙")):
            with self.subTest(worker=worker):
                run = self.command("start", "--project", str(self.project), "--id", "S5" + worker, "--brief",
                                   brief.name, "--worker", worker, "--instruction", "AGENTS.md",
                                   "--instruction", "CLAUDE.md", "--instruction", "rules.md")
                passed = "CLAUDE.md" if worker == "codex" else "AGENTS.md"
                self.assertEqual(run["instructions"], [str(self.project / passed), str(self.project / "rules.md")])
                prompt = (Path(run["run_dir"]) / "prompt.txt").read_text(encoding="utf-8")
                self.assertEqual(prompt.count(other), 1)
                self.assertEqual(prompt.count(self.instructions), 1)
                self.assertNotIn(own, prompt)

    def test_tier_and_worker_options_pick_the_model(self):
        runner = load_runner()
        default = self.launch("S7")
        expected_worker = runner.default_worker()
        self.assertEqual((default["worker"], default["model"]),
                         (expected_worker, runner.TIERS[expected_worker]["implement"][0]))
        self.assertTrue(Path(default["cli"]).name == expected_worker)
        light = self.launch("S8", "작업", "--worker", "claude", "--tier", "light")
        self.assertEqual((light["worker"], light["model"], light["effort"]), ("claude", "sonnet", "medium"))
        custom = self.launch("S9", "작업", "--worker", "codex", "--tier", "reason", "--model", "gpt-6-luna", "--effort", "high")
        self.assertEqual((custom["model"], custom["effort"]), ("gpt-6-luna", "high"))
        for run in (light, custom):
            self.wait_file(Path(run["report"]))
        captured = json.loads((Path(light["report"]).parent / "argv.json").read_text())
        self.assertEqual(captured["cwd"], str(self.project))
        self.assertEqual(captured["args"][:-1], ["-p", "--model", "sonnet", "--effort", "medium",
                                                 "--permission-mode", "bypassPermissions", "--output-format", "text"])
        self.assertEqual(captured["args"][-1], (Path(light["run_dir"]) / "prompt.txt").read_text())
        captured = json.loads((Path(custom["report"]).parent / "argv.json").read_text())
        self.assertEqual(captured["args"][5:9], ["-m", "gpt-6-luna", "-c", 'model_reasoning_effort="high"'])
        rows = {row["id"]: row for row in self.status("--tail", "0")["runs"]}
        self.assertEqual((rows["S8"]["model"], rows["S9"]["model"]), ("sonnet", "gpt-6-luna"))
        self.assertIn("--worker", self.launch("S10", "작업", "--worker", "gemini", expected=2).stderr)

    def test_disallowed_model_fails_before_launch(self):
        result = self.launch("S1", "작업", "--worker", "codex", "--model", "gpt-6-astra", expected=1)
        self.assertIn("허용 모델", result.stderr)
        self.assertFalse((self.project / ".git/harness-runs").exists())

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root는 읽기 전용 권한을 무시함")
    def test_unwritable_git_directory_explains_sandbox_escalation(self):
        git_dir = self.project / ".git"
        git_dir.chmod(0o555)
        self.addCleanup(git_dir.chmod, 0o755)
        result = self.launch("S6", expected=1)
        self.assertIn("권한 상승", result.stderr)
        self.assertFalse((git_dir / "harness-runs").exists())

    def test_missing_material_fails_before_creating_run(self):
        (self.project / "rules.md").unlink()
        self.launch("S4", expected=1)
        self.assertFalse((self.project / ".git/harness-runs").exists())


if __name__ == "__main__":
    unittest.main()
