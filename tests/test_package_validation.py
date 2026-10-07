import json
from pathlib import Path
import shutil
import tempfile
import unittest

from package_validation import validate_package

from target import source_root

ROOT = source_root()


class PackageValidationTests(unittest.TestCase):
    def setUp(self):
        self.storage = tempfile.TemporaryDirectory()
        self.addCleanup(self.storage.cleanup)
        self.root = Path(self.storage.name) / "package"
        self.root.mkdir()
        for directory in ("skills", "docs", "config", ".agents", ".claude-plugin", ".github", "tests/behavioral/cases"):
            if (ROOT / directory).exists():
                shutil.copytree(ROOT / directory, self.root / directory)
        for filename in ("README.md", "plugin.json"):
            shutil.copy2(ROOT / filename, self.root / filename)

    def edit_json(self, filename, change):
        path = self.root / filename
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))

    def assert_diagnostic(self, filename, text):
        self.assertTrue(any(message.startswith(filename + ":") and text in message
                            for message in validate_package(self.root)), validate_package(self.root))

    def test_real_repository_passes(self):
        self.assertEqual(validate_package(ROOT), [])

    def test_declarative_library_rejects_scripts_tests_and_evidence(self):
        for name in ("helper.py", "skills/setup/scripts/helper.sh", "tests/example.txt", "docs/evidence/result.json", "hooks/hook.json"):
            with self.subTest(name=name):
                path = self.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture")
                self.assertTrue(any("declarative library" in error for error in validate_package(self.root)))
                path.unlink()
                parent = path.parent
                while parent != self.root and not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
        guide = self.root / "skills/setup/references/task.md"
        guide.parent.mkdir(parents=True, exist_ok=True)
        guide.write_text("Use inherited settings for this task.\n")
        self.assertEqual(validate_package(self.root), [])

    def test_validation_leaves_package_unchanged(self):
        before = {path.relative_to(self.root): path.read_bytes()
                  for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(validate_package(self.root), [])
        after = {path.relative_to(self.root): path.read_bytes()
                 for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(after, before)

    def test_supported_changes_pass(self):
        for filename in ("plugin.json", ".claude-plugin/plugin.json"):
            self.edit_json(filename, lambda data: data.update(version="1.2.3-rc.1+build.2", description="Different useful description"))
        self.edit_json(".claude-plugin/marketplace.json", lambda data: data["plugins"][0].update(version="1.2.3-rc.1+build.2", description="Different useful description"))
        self.edit_json(".claude-plugin/marketplace.json", lambda data: data["metadata"].update(description="Different useful description"))
        path = self.root / "README.md"
        path.write_text(path.read_text() + "\nRepeat `$pancake-stack:fix`. [Directory](skills/) [fragment](#here) [encoded](docs/%72ecipes.md)\n")
        self.assertEqual(validate_package(self.root), [])

    def test_invalid_json_and_duplicates(self):
        for filename, content, expected in (
            ("plugin.json", "{", "invalid JSON"),
            (".agents/plugins/marketplace.json", '{"plugins":[],"plugins":[]}', "duplicate JSON key"),
            ("config/preferences.example.json", '{"defaults":{"model":null,"model":null}}', "duplicate JSON key"),
        ):
            with self.subTest(filename=filename):
                (self.root / filename).parent.mkdir(parents=True, exist_ok=True)
                (self.root / filename).write_text(content)
                self.assert_diagnostic(filename, expected)

    def test_marketplace_identity_and_source(self):
        filename = ".agents/plugins/marketplace.json"
        self.edit_json(filename, lambda data: data["plugins"][0].update(name="other"))
        self.assert_diagnostic(filename, "name must match")
        self.edit_json(filename, lambda data: data["plugins"][0]["source"].update(path="../"))
        self.assert_diagnostic(filename, "source must be local ./")

    def test_invalid_manifest_shapes(self):
        for field, value, expected in (("version", "01.2.3", "semantic version"), ("description", " ", "nonempty"), ("author", [], "author must"), ("extensions", [], "interface must"), ("$schema", "other", "schema URL")):
            with self.subTest(field=field):
                original = (self.root / "plugin.json").read_text()
                self.edit_json("plugin.json", lambda data: data.update({field: value}))
                self.assert_diagnostic("plugin.json", expected)
                (self.root / "plugin.json").write_text(original)

    def test_claude_contracts_and_metadata_drift(self):
        cases = (
            (".claude-plugin/plugin.json", lambda data: data.update(skills="../skills"), "shared ./skills/"),
            (".claude-plugin/plugin.json", lambda data: data.update(version="0.0.0"), "version must match"),
            (".claude-plugin/plugin.json", lambda data: data.update(hooks={}), "native Claude manifest fields"),
            (".claude-plugin/marketplace.json", lambda data: data["plugins"][0].update(source="../"), "source must be ./"),
            (".claude-plugin/marketplace.json", lambda data: data["plugins"][0].update(description="drift"), "description must match"),
            (".claude-plugin/marketplace.json", lambda data: data.update(owner={"name": "other"}), "owner must match"),
            (".claude-plugin/marketplace.json", lambda data: data.update(plugins=[]), "one local package entry"),
            (".claude-plugin/marketplace.json", lambda data: data.update(metadata={}), "marketplace description must match"),
        )
        for filename, change, expected in cases:
            with self.subTest(filename=filename, expected=expected):
                path = self.root / filename
                original = path.read_text()
                self.edit_json(filename, change)
                self.assert_diagnostic(filename, expected)
                path.write_text(original)
        for filename in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
            path = self.root / filename
            original = path.read_text()
            path.write_text('{"name":"a","name":"b"}')
            self.assert_diagnostic(filename, "duplicate JSON key")
            path.write_text(original)

    def test_skill_frontmatter_and_missing_file(self):
        filename = "skills/fix/SKILL.md"
        path = self.root / filename
        for header, expected in (("name: other\ndescription: text", "name must match"), ("name: fix\nname: fix\ndescription: text", "duplicate frontmatter"), ("name: fix\ndescription: |\n  text", "unsupported frontmatter"), ("name: fix\ndescription: \"text\"", "unsupported frontmatter"), ("name: fix\ndescription: " + "a" * 1025, "1 to 1024")):
            with self.subTest(expected=expected):
                path.write_text("---\n" + header + "\n---\n")
                self.assert_diagnostic(filename, expected)
        path.unlink()
        self.assert_diagnostic("README.md", "unknown documented skill fix")

    def test_readme_skill_coverage(self):
        path = self.root / "README.md"
        path.write_text(path.read_text().replace("$pancake-stack:fix", "$pancake-stack:unknown"))
        self.assert_diagnostic("README.md", "missing documented skill fix")
        self.assert_diagnostic("README.md", "unknown documented skill unknown")

    def test_picker_metadata_missing_and_escaping_file(self):
        filename = "skills/setup/agents/openai.yaml"
        path = self.root / filename
        path.unlink()
        self.assert_diagnostic(filename, "cannot read file")
        path.symlink_to(Path(self.storage.name) / "outside.yaml")
        self.assert_diagnostic(filename, "path escapes package")

    def test_picker_metadata_structure_and_values(self):
        filename = "skills/setup/agents/openai.yaml"
        valid = 'interface:\n  display_name: "Setup"\n  short_description: "Choose models"\n'
        cases = (
            ("", "expected interface mapping"),
            (valid.replace("interface:", "interface: []"), "expected interface mapping"),
            (valid.replace('  display_name: "Setup"\n', ""), "missing interface.display_name"),
            (valid.replace('  short_description: "Choose models"\n', ""), "missing interface.short_description"),
            (valid + '  display_name: "Again"\n', "duplicate interface field"),
            (valid + 'unknown: "value"\n', "unsupported picker syntax"),
            (valid.replace("  display_name", "    display_name"), "unsupported picker syntax"),
            (valid.replace('"Setup"', '"unterminated'), "unsupported picker syntax"),
            (valid.replace('"Setup"', '"bad\\q"'), "invalid quoted string"),
            (valid.replace('"Setup"', '""'), "nonempty single-line text"),
            (valid.replace('"Setup"', '"  "'), "nonempty single-line text"),
            (valid.replace('"Setup"', '"line\\nline"'), "nonempty single-line text"),
            (valid.replace('"Setup"', "true"), "unsupported picker syntax"),
            (valid.replace('"Setup"', "[Setup]"), "unsupported picker syntax"),
        )
        for content, diagnostic in cases:
            with self.subTest(content=content):
                (self.root / filename).parent.mkdir(parents=True, exist_ok=True)
                (self.root / filename).write_text(content)
                self.assert_diagnostic(filename, diagnostic)
        (self.root / filename).write_text(
            'interface:\n  short_description: "Explain the learner’s \\"code\\""\n  display_name: "A different name"\n'
        )
        self.assertEqual(validate_package(self.root), [])

    def test_yaml_syntax_and_non_string_scalars_are_rejected(self):
        filename = "skills/fix/SKILL.md"
        for value in ("true", "NO", "null", "123", "2026-10-03", "text: more", "text:", "# comment", "text\t# comment", "&anchor text", "!tag text"):
            with self.subTest(value=value):
                (self.root / filename).write_text("---\nname: fix\ndescription: " + value + "\n---\n")
                self.assert_diagnostic(filename, "unsupported frontmatter")

    def test_missing_and_escaping_references(self):
        path = self.root / "skills/fix/SKILL.md"
        path.write_text(path.read_text() + "\n[Missing](missing.md) [Escaping](../../../outside.md)\n")
        self.assert_diagnostic("skills/fix/SKILL.md", "missing relative link")
        self.assert_diagnostic("skills/fix/SKILL.md", "escapes package")

    def test_symlink_reference_escape(self):
        (self.root / "docs/external.md").symlink_to(Path(self.storage.name) / "outside.md")
        path = self.root / "README.md"
        path.write_text(path.read_text() + "\n[Outside](docs/external.md)\n")
        self.assert_diagnostic("README.md", "escapes package")


if __name__ == "__main__":
    unittest.main()
