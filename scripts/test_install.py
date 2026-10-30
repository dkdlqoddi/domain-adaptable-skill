"""설치 충돌·보존·호환 형식·ZIP 배포를 임시 프로젝트에서 검증한다."""
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

    def assert_links_exist(self, directory):
        for path in directory.rglob("*.md"):
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if not link.startswith(("http:", "https:", "#")):
                    self.assertTrue((path.parent / link).is_file(), (path, link))

    def test_fresh_and_repeat_are_identical(self):
        self.install()
        before = snapshot(self.project)
        self.assertEqual(len(list((self.project / ".claude/skills").glob("*/SKILL.md"))), 5)
        self.assertEqual(len(list((self.project / "docs").rglob("*.md"))), 10)
        self.install()
        self.assertEqual(snapshot(self.project), before)

    def test_existing_root_rules_use_dot_claude(self):
        self.write("CLAUDE.md", "user rules\n")
        self.install()
        self.assertEqual((self.project / "CLAUDE.md").read_text(), "user rules\n")
        self.assertEqual((self.project / ".claude/CLAUDE.md").read_bytes(),
                         (ROOT / "harness/CLAUDE.md").read_bytes())
        before = snapshot(self.project)
        self.install()
        self.assertEqual(snapshot(self.project), before)

    def test_both_rules_conflict_without_any_writes(self):
        self.write("CLAUDE.md", "root rules\n")
        self.write(".claude/CLAUDE.md", "dot rules\n")
        before = snapshot(self.project)
        self.install(expected=2)
        self.assertEqual(snapshot(self.project), before)

    def test_skill_conflict_is_not_partial_success(self):
        self.write(".claude/skills/spec/SKILL.md", "custom spec\n")
        before = snapshot(self.project)
        self.install(expected=2)
        self.assertEqual(snapshot(self.project), before)

    def test_force_backs_up_rules_and_skills_but_keeps_state(self):
        self.write("CLAUDE.md", "root rules\n")
        self.write(".claude/CLAUDE.md", "dot rules\n")
        self.write(".claude/skills/spec/SKILL.md", "custom spec\n")
        self.write("docs/SPEC.md", "user task state\n")
        self.install("--force")
        backups = list((self.project / ".harness-backups").iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / ".claude/CLAUDE.md").read_text(), "dot rules\n")
        self.assertEqual((backups[0] / ".claude/skills/spec/SKILL.md").read_text(), "custom spec\n")
        self.assertEqual((self.project / "CLAUDE.md").read_text(), "root rules\n")
        self.assertEqual((self.project / "docs/SPEC.md").read_text(), "user task state\n")
        before = snapshot(self.project)
        self.install("--force")
        self.assertEqual(snapshot(self.project), before)

    def test_harness_rule_update_does_not_create_a_second_copy(self):
        self.write("CLAUDE.md", "# 작업 헌법 (프로젝트 루트)\nold harness\n")
        self.install(expected=2)
        self.install("--force")
        self.assertFalse((self.project / ".claude/CLAUDE.md").exists())

    def test_partial_docs_are_filled_without_overwrite(self):
        self.write("docs/SPEC.md", "existing spec\n")
        self.install()
        self.assertEqual((self.project / "docs/SPEC.md").read_text(), "existing spec\n")
        self.assertTrue((self.project / "docs/TASKS.md").is_file())

    def test_codex_preserves_conflicting_agents_by_default(self):
        self.write("AGENTS.md", "user agent rules\n")
        before = snapshot(self.project)
        self.install("--tool", "codex", expected=2)
        self.assertEqual(snapshot(self.project), before)
        self.install("--tool", "codex", "--force")
        saved = list((self.project / ".harness-backups").glob("*/AGENTS.md"))
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].read_text(), "user agent rules\n")

    def test_codex_conversion_and_reinstallation(self):
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

    def test_legacy_commands_resolve_supporting_files(self):
        self.install("--tool", "claude-commands")
        commands = self.project / ".claude/commands"
        self.assertEqual(len(list(commands.glob("*.md"))), 5)
        self.assert_links_exist(commands)
        kickoff = (commands / "kickoff.md").read_text()
        self.assertNotIn("${CLAUDE_SKILL_DIR}", kickoff)
        self.assertIn(".claude/skills/kickoff/templates/docs/.", kickoff)
        before = snapshot(self.project)
        self.install("--tool", "claude-commands")
        self.assertEqual(snapshot(self.project), before)

    def test_symlink_is_not_followed_even_with_force(self):
        external = self.base / "external"
        external.mkdir()
        (self.project / ".claude").symlink_to(external, target_is_directory=True)
        self.install("--force", expected=1)
        self.assertEqual(snapshot(external), {})
        self.assertFalse((self.project / "CLAUDE.md").exists())

    def test_directory_instead_of_file_fails_before_writes(self):
        (self.project / "docs/SPEC.md").mkdir(parents=True)
        self.install("--force", expected=1)
        self.assertFalse((self.project / ".claude").exists())

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
            self.assertNotIn("CLAUDE.md", archive.namelist())
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
        self.project = self.base / "packaged conflict"
        self.project.mkdir()
        self.write("CLAUDE.md", "root rules\n")
        self.write(".claude/CLAUDE.md", "dot rules\n")
        before = snapshot(self.project)
        self.install(script=extracted / "scripts/install.sh", expected=2)
        self.assertEqual(snapshot(self.project), before)


if __name__ == "__main__":
    unittest.main()
