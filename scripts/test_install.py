"""Codex 원본 설치·충돌·보존·Claude 호환 형식·ZIP 배포를 검증한다."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / "scripts/install.sh"


def snapshot(directory):
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in directory.rglob("*") if p.is_file()}


class InstallationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="harness-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.project = self.base / "과제 project"
        self.project.mkdir()

    def install(self, *options, expected=0, script=INSTALL):
        result = subprocess.run(["bash", str(script), str(self.project), *options],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def write(self, relative, data):
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")

    def assert_links_exist(self, directory, root=None):
        for path in directory.rglob("*.md"):
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if not link.startswith(("http:", "https:", "#")):
                    self.assertTrue(((root or path.parent) / link).is_file(), (path, link))

    def test_fresh_and_repeat_are_identical(self):
        self.install()
        before = snapshot(self.project)
        self.assertEqual(len(list((self.project / ".agents/skills").glob("*/SKILL.md"))), 5)
        templates = ROOT / "harness/.agents/skills/kickoff/templates/docs"
        self.assertEqual(snapshot(self.project / "docs"), snapshot(templates))
        for relative, data in snapshot(ROOT / "harness").items():
            self.assertEqual(before[relative], data, relative)
        self.assertFalse((self.project / ".claude").exists())
        self.assertFalse((self.project / "CLAUDE.md").exists())
        self.install()
        self.assertEqual(snapshot(self.project), before)

    def test_explicit_codex_is_the_default(self):
        self.install()
        before = snapshot(self.project)
        self.install("--tool", "codex")
        self.assertEqual(snapshot(self.project), before)

    def test_existing_root_rules_use_dot_claude(self):
        self.write("CLAUDE.md", "user rules\n")
        self.install("--tool", "claude")
        self.assertEqual((self.project / "CLAUDE.md").read_text(), "user rules\n")
        self.assertIn(".claude/skills/", (self.project / ".claude/CLAUDE.md").read_text())
        before = snapshot(self.project)
        self.install("--tool", "claude")
        self.assertEqual(snapshot(self.project), before)

    def test_both_rules_conflict_without_any_writes(self):
        self.write("CLAUDE.md", "root rules\n")
        self.write(".claude/CLAUDE.md", "dot rules\n")
        before = snapshot(self.project)
        self.install("--tool", "claude", expected=2)
        self.assertEqual(snapshot(self.project), before)

    def test_skill_conflict_is_not_partial_success(self):
        self.write(".agents/skills/spec/SKILL.md", "custom spec\n")
        before = snapshot(self.project)
        self.install(expected=2)
        self.assertEqual(snapshot(self.project), before)

    def test_force_backs_up_rules_and_skills_but_keeps_state(self):
        self.write("AGENTS.md", "root rules\n")
        self.write(".agents/skills/spec/SKILL.md", "custom spec\n")
        self.write("docs/SPEC.md", "user task state\n")
        self.install("--force")
        backups = list((self.project / ".harness-backups").iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "AGENTS.md").read_text(), "root rules\n")
        self.assertEqual((backups[0] / ".agents/skills/spec/SKILL.md").read_text(), "custom spec\n")
        self.assertEqual((self.project / "docs/SPEC.md").read_text(), "user task state\n")
        before = snapshot(self.project)
        self.install("--force")
        self.assertEqual(snapshot(self.project), before)

    def test_harness_rule_update_does_not_create_a_second_copy(self):
        self.write("CLAUDE.md", "# 작업 헌법 (프로젝트 루트)\nold harness\n")
        self.install("--tool", "claude", expected=2)
        self.install("--tool", "claude", "--force")
        self.assertFalse((self.project / ".claude/CLAUDE.md").exists())

    def test_partial_docs_are_filled_without_overwrite(self):
        self.write("docs/SPEC.md", "existing spec\n")
        self.install()
        self.assertEqual((self.project / "docs/SPEC.md").read_text(), "existing spec\n")
        self.assertTrue((self.project / "docs/TASKS.md").is_file())

    def test_learning_docs_survive_force_and_runner_is_copied_for_every_tool(self):
        source = ROOT / "harness/.agents/skills/delegate/scripts/tmux_codex.py"
        for tool, prefix in (("codex", ".agents"), ("claude", ".claude"), ("claude-commands", ".claude")):
            with self.subTest(tool=tool):
                self.project = self.base / tool
                self.project.mkdir()
                for name in ("KNOWLEDGE.md", "QUIZ.md", "QUIZ-ANSWERS.md"):
                    self.write("docs/" + name, "사용자가 이미 쓴 내용: " + name)
                self.install("--tool", tool, "--force")
                for name in ("KNOWLEDGE.md", "QUIZ.md", "QUIZ-ANSWERS.md"):
                    self.assertEqual((self.project / "docs" / name).read_text(), "사용자가 이미 쓴 내용: " + name)
                installed = self.project / prefix / "skills/delegate/scripts/tmux_codex.py"
                self.assertEqual(installed.read_bytes(), source.read_bytes())
                result = subprocess.run(["python3", "-B", str(installed), "start", "--help"],
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_codex_preserves_conflicting_agents_by_default(self):
        self.write("AGENTS.md", "user agent rules\n")
        before = snapshot(self.project)
        self.install("--tool", "codex", expected=2)
        self.assertEqual(snapshot(self.project), before)
        self.install("--tool", "codex", "--force")
        saved = list((self.project / ".harness-backups").glob("*/AGENTS.md"))
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].read_text(), "user agent rules\n")

    def test_codex_skills_and_reinstallation(self):
        self.install("--tool", "codex")
        skills = self.project / ".agents/skills"
        self.assertEqual(len(list(skills.glob("*/SKILL.md"))), 5)
        for skill in skills.glob("*/SKILL.md"):
            text = skill.read_text()
            self.assertNotIn("disable-model-invocation:", text)
            self.assertNotIn("argument-hint:", text)
            self.assertNotIn("$ARGUMENTS", text)
            self.assertNotIn("${CLAUDE_SKILL_DIR}", text)
            self.assertIn("allow_implicit_invocation: false", (skill.parent / "agents/openai.yaml").read_text())
        self.assertIn("$kickoff", (skills / "kickoff/SKILL.md").read_text())
        self.assertIn("/new", (self.project / "AGENTS.md").read_text())
        self.assertTrue((skills / "spec/module-agents.template.md").is_file())
        self.assert_links_exist(skills)
        before = snapshot(self.project)
        self.install("--tool", "codex")
        self.assertEqual(snapshot(self.project), before)
        self.assertFalse((skills / "skills").exists())
        self.assertFalse((self.project / ".claude").exists())

    def test_codex_payload_has_no_claude_instructions(self):
        self.install()
        for path in self.project.rglob("*.md"):
            with self.subTest(path=path.relative_to(self.project)):
                text = path.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"CLAUDE|\.claude|module-claude|\$ARGUMENTS")
                self.assertNotRegex(text, r"disable-model-invocation:|argument-hint:")
                self.assertNotRegex(text, r"/(?:kickoff|interview|spec|delegate|wrapup)\b(?!/)")
                self.assertNotIn("/clear", text)

    def test_codex_policy_conflict_is_backed_up(self):
        policy = ".agents/skills/interview/agents/openai.yaml"
        original = "policy:\n  allow_implicit_invocation: true\n"
        self.write(policy, original)
        before = snapshot(self.project)
        self.install(expected=2)
        self.assertEqual(snapshot(self.project), before)
        self.install("--force")
        saved = list((self.project / ".harness-backups").glob("*/" + policy))
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].read_text(), original)

    def test_claude_conversion_has_usable_skills_and_templates(self):
        self.install("--tool", "claude")
        skills = self.project / ".claude/skills"
        self.assertEqual(len(list(skills.glob("*/SKILL.md"))), 5)
        self.assertFalse((self.project / ".agents").exists())
        self.assertFalse((self.project / "AGENTS.md").exists())
        for skill in skills.glob("*/SKILL.md"):
            text = skill.read_text()
            self.assertIn("disable-model-invocation: true", text.split("---", 2)[1])
            self.assertFalse((skill.parent / "agents/openai.yaml").exists())
        for path in self.project.rglob("*.md"):
            self.assertNotRegex(path.read_text(), r"AGENTS\.md|\.agents/|\$(?:kickoff|interview|spec|delegate|wrapup)\b|/new\b")
        self.assertTrue((skills / "spec/module-claude.template.md").is_file())
        self.assert_links_exist(skills)

    def test_legacy_commands_resolve_supporting_files(self):
        self.install("--tool", "claude-commands")
        commands = self.project / ".claude/commands"
        self.assertEqual(len(list(commands.glob("*.md"))), 5)
        # 명령 본문에는 파일 위치 정보가 없어 모델이 링크를 프로젝트 루트 기준으로 연다.
        self.assert_links_exist(commands, root=self.project)
        self.assertNotIn("](../", "".join(p.read_text() for p in commands.glob("*.md")))
        kickoff = (commands / "kickoff.md").read_text()
        self.assertNotIn("${CLAUDE_SKILL_DIR}", kickoff)
        self.assertIn(".claude/skills/kickoff/templates/docs/.", kickoff)
        before = snapshot(self.project)
        self.install("--tool", "claude-commands")
        self.assertEqual(snapshot(self.project), before)

    def test_symlink_is_not_followed_even_with_force(self):
        for tool, directory in (("codex", ".agents"), ("claude", ".claude")):
            with self.subTest(tool=tool):
                self.project = self.base / (tool + " symlink")
                self.project.mkdir()
                external = self.base / (tool + " external")
                external.mkdir()
                (self.project / directory).symlink_to(external, target_is_directory=True)
                self.install("--tool", tool, "--force", expected=1)
                self.assertEqual(snapshot(external), {})
                self.assertFalse((self.project / "AGENTS.md").exists())
                self.assertFalse((self.project / "CLAUDE.md").exists())

    def test_directory_instead_of_file_fails_before_writes(self):
        (self.project / "docs/SPEC.md").mkdir(parents=True)
        self.install("--force", expected=1)
        self.assertFalse((self.project / ".agents").exists())

    def test_invalid_option_does_not_install(self):
        self.install("--unknown", expected=2)
        self.assertEqual(snapshot(self.project), {})

    def test_zip_uses_identical_installer_for_every_tool(self):
        repo = self.base / "package source"
        shutil.copytree(ROOT / "harness", repo / "harness")
        (repo / "scripts").mkdir()
        for name in ("install.sh", "install.py", "pack.sh"):
            shutil.copy2(ROOT / "scripts" / name, repo / "scripts" / name)
        result = subprocess.run(["bash", str(repo / "scripts/pack.sh")], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        extracted = self.base / "unpacked"
        with zipfile.ZipFile(repo / "dist/harness.zip") as archive:
            self.assertIsNone(archive.testzip())
            self.assertNotIn("AGENTS.md", archive.namelist())
            self.assertIn("harness/AGENTS.md", archive.namelist())
            self.assertFalse(any(".claude" in name for name in archive.namelist()))
            archive.extractall(extracted)
        for tool in ("claude", "claude-commands", "codex"):
            self.project = self.base / (tool + " direct")
            self.project.mkdir()
            self.install("--tool", tool)
            direct = snapshot(self.project)
            self.project = self.base / (tool + " packaged")
            self.project.mkdir()
            self.install("--tool", tool, script=extracted / "scripts/install.sh")
            self.assertEqual(snapshot(self.project), direct)
        self.project = self.base / "packaged default"
        self.project.mkdir()
        self.install(script=extracted / "scripts/install.sh")
        self.assertEqual(snapshot(self.project), snapshot(self.base / "codex direct"))
        self.project = self.base / "packaged conflict"
        self.project.mkdir()
        self.write("AGENTS.md", "root rules\n")
        before = snapshot(self.project)
        self.install(script=extracted / "scripts/install.sh", expected=2)
        self.assertEqual(snapshot(self.project), before)


if __name__ == "__main__":
    unittest.main()
