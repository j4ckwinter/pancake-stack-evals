"""Read-only checks for this repository's package conventions, not a schema validator.

Skill headers support only plain, unquoted, single-line name and description.
Header values begin with an ASCII letter; YAML scalar literals are unsupported.
Picker metadata supports an interface mapping with exactly display_name and
short_description, using two-space indentation and JSON-style quoted strings.
This deliberately restricted YAML subset is a repository convention.
Markdown checks cover relative inline links, not reference-style links or anchors.
"""

import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SEMVER = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?\Z"
)
LINK = re.compile(r"\[[^\]\n]*\]\((<[^>\n]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\)")
SCALAR_LITERALS = {"true", "false", "yes", "no", "on", "off", "null"}


def validate_package(root: Path) -> list[str]:
    """Return file-specific diagnostics without modifying files or invoking hosts."""
    root = root.resolve()
    errors = []

    def fail(path, message):
        errors.append(f"{path.relative_to(root)}: {message}")

    for directory in (root / "tests", root / "docs/evidence", root / "hooks"):
        if directory.exists():
            fail(directory, "evaluation tools, evidence, and hooks do not belong in the declarative library")
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        if path.suffix == ".py" or (relative.parts[0] == "skills" and "scripts" in relative.parts):
            fail(path, "bundled executable helpers do not belong in the declarative library")

    def read(path):
        if not path.resolve().is_relative_to(root):
            fail(path, "path escapes package")
            return None
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            fail(path, f"cannot read file ({error})")
            return None

    def json_object(path):
        source = read(path)
        if source is None:
            return {}

        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise ValueError(f"duplicate JSON key {key!r}")
                result[key] = value
            return result

        def reject_constant(value):
            raise ValueError(f"invalid JSON constant {value}")

        try:
            result = json.loads(source, object_pairs_hook=pairs, parse_constant=reject_constant)
            if not isinstance(result, dict):
                raise ValueError("expected JSON object")
            return result
        except ValueError as error:
            fail(path, f"invalid JSON ({error})")
            return {}

    def nonempty(value):
        return isinstance(value, str) and bool(value.strip())

    manifest_path = root / "plugin.json"
    manifest = json_object(manifest_path)
    name = manifest.get("name")
    if manifest.get("$schema") != SCHEMA:
        fail(manifest_path, "expected declared portable schema URL")
    if not isinstance(name, str) or not NAME.fullmatch(name):
        fail(manifest_path, "name must be a lowercase hyphenated identifier")
    if not nonempty(manifest.get("description")):
        fail(manifest_path, "description must be a nonempty string")
    version = manifest.get("version")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        fail(manifest_path, "version must be semantic version text")
    author = manifest.get("author")
    if not isinstance(author, dict) or not nonempty(author.get("name")):
        fail(manifest_path, "author must be an object with a nonempty name")
    extensions = manifest.get("extensions")
    openai = extensions.get("com.openai") if isinstance(extensions, dict) else None
    interface = openai.get("interface") if isinstance(openai, dict) else None
    if not isinstance(interface, dict):
        fail(manifest_path, "extensions.com.openai.interface must be an object")
    else:
        for field in ("displayName", "shortDescription", "developerName", "category"):
            if not nonempty(interface.get(field)):
                fail(manifest_path, f"interface.{field} must be a nonempty string")

    marketplace_path = root / ".agents/plugins/marketplace.json"
    marketplace = json_object(marketplace_path)
    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
        fail(marketplace_path, "expected one local package entry")
    else:
        entry = entries[0]
        if entry.get("name") != name:
            fail(marketplace_path, "plugin entry name must match plugin.json")
        source = entry.get("source")
        if not isinstance(source, dict) or source.get("source") != "local" or source.get("path") != "./":
            fail(marketplace_path, "package source must be local ./")
        elif (root / source["path"]).resolve() != root:
            fail(marketplace_path, "local source does not resolve to package root")

    claude_path = root / ".claude-plugin/plugin.json"
    claude = json_object(claude_path)
    for field in ("name", "version", "description", "author"):
        if claude.get(field) != manifest.get(field):
            fail(claude_path, f"{field} must match plugin.json")
    if claude.get("skills") != "./skills/":
        fail(claude_path, "skills must point to shared ./skills/")
    elif not (root / claude["skills"]).resolve().is_relative_to(root):
        fail(claude_path, "skills path escapes package")
    if set(claude) != {"name", "version", "description", "author", "skills"}:
        fail(claude_path, "expected native Claude manifest fields")

    claude_market_path = root / ".claude-plugin/marketplace.json"
    claude_market = json_object(claude_market_path)
    if claude_market.get("name") != name:
        fail(claude_market_path, "marketplace name must match plugin.json")
    if claude_market.get("owner") != author:
        fail(claude_market_path, "owner must match plugin author")
    metadata = claude_market.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("description") != manifest.get("description"):
        fail(claude_market_path, "marketplace description must match plugin.json")
    claude_entries = claude_market.get("plugins")
    if not isinstance(claude_entries, list) or len(claude_entries) != 1 or not isinstance(claude_entries[0], dict):
        fail(claude_market_path, "expected one local package entry")
    else:
        entry = claude_entries[0]
        for field in ("name", "version", "description", "author"):
            if entry.get(field) != manifest.get(field):
                fail(claude_market_path, f"plugin entry {field} must match plugin.json")
        if entry.get("source") != "./":
            fail(claude_market_path, "package source must be ./")
        elif (root / entry["source"]).resolve() != root:
            fail(claude_market_path, "local source does not resolve to package root")

    for path in sorted((root / "config").glob("*.example.json")):
        json_object(path)

    skills = set()
    for path in sorted((root / "skills").glob("*/SKILL.md")):
        directory = path.parent
        picker_path = directory / "agents/openai.yaml"
        picker = read(picker_path)
        if picker is not None:
            picker_lines = picker.splitlines()
            picker_fields = {}
            if not picker_lines or picker_lines[0] != "interface:":
                fail(picker_path, "expected interface mapping")
            for line in picker_lines[1:]:
                match = re.fullmatch(r"  (display_name|short_description): (\".*\")", line)
                if not match:
                    fail(picker_path, "unsupported picker syntax; use two-space indented fields and JSON-style quoted strings")
                    continue
                key, literal = match.groups()
                if key in picker_fields:
                    fail(picker_path, f"duplicate interface field {key}")
                picker_fields[key] = None
                try:
                    value = json.loads(literal)
                except ValueError:
                    fail(picker_path, f"invalid quoted string for interface.{key}")
                    continue
                if not nonempty(value) or any(ord(char) < 32 for char in value):
                    fail(picker_path, f"interface.{key} must be nonempty single-line text")
                picker_fields[key] = value
            for missing in {"display_name", "short_description"} - picker_fields.keys():
                fail(picker_path, f"missing interface.{missing}")
        text = read(path)
        skills.add(directory.name)
        if text is None:
            continue
        lines = text.splitlines()
        if not lines or lines[0] != "---" or "---" not in lines[1:]:
            fail(path, "missing delimited frontmatter")
            continue
        fields = {}
        for line in lines[1:lines.index("---", 1)]:
            match = re.fullmatch(r"(name|description): (\S.*)", line)
            if (not match or not re.match(r"[A-Za-z]", match[2])
                    or match[2].strip().lower() in SCALAR_LITERALS
                    or re.search(r":(?:\s|$)|\s#", match[2])):
                fail(path, "unsupported frontmatter; use plain unquoted single-line name and description")
                continue
            key, value = match.groups()
            if key in fields:
                fail(path, f"duplicate frontmatter field {key}")
            fields[key] = value
        if fields.get("name") != directory.name or not NAME.fullmatch(fields.get("name", "")) or len(fields.get("name", "")) > 64:
            fail(path, "name must match directory and be a lowercase identifier of at most 64 characters")
        if not fields.get("description", "").strip() or len(fields.get("description", "")) > 1024:
            fail(path, "description must contain 1 to 1024 characters")

    readme_path = root / "README.md"
    readme = read(readme_path)
    if readme is not None and isinstance(name, str):
        mentioned = set(re.findall(r"\$" + re.escape(name) + r":([a-z0-9-]+)", readme))
        for missing in sorted(skills - mentioned):
            fail(readme_path, f"missing documented skill {missing}")
        for extra in sorted(mentioned - skills):
            fail(readme_path, f"unknown documented skill {extra}")

    documents = [readme_path, *sorted((root / "docs").rglob("*.md")), *sorted((root / "skills").rglob("*.md"))]
    for path in documents:
        source = read(path)
        if source is None:
            continue
        for match in LINK.finditer(source):
            target = match[1].strip("<>")
            try:
                parsed = urlsplit(target)
            except ValueError:
                fail(path, f"invalid inline link target: {target}")
                continue
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            destination = (path.parent / unquote(parsed.path)).resolve()
            if not destination.is_relative_to(root):
                fail(path, f"relative link escapes package: {target}")
            elif not destination.exists():
                fail(path, f"missing relative link target: {target}")
    return errors
