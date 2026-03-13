#!/usr/bin/env python3
"""
Skills — Task Structure Validator

Checks every structural requirement for a task directory.
Exits 0 if all required checks pass, 1 if any errors are found.

Usage:
    python validate_task.py --task-path tasks/my-task
    python validate_task.py --task-name my-task           # looks under tasks/
"""
import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Output helpers — Errors: format the CI parser expects
# ---------------------------------------------------------------------------

errors: list[str] = []


def error(msg: str) -> None:
    errors.append(msg)


def print_results(task_name: str) -> None:
    if not errors:
        print(f"All checks passed for task: {task_name}")
        return
    print("Errors:")
    for e in errors:
        print(f"  - {e}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        error(f"{path.name} is not valid JSON: {e}")
        return None
    except FileNotFoundError:
        return None


def parse_frontmatter(skill_md: Path) -> dict:
    """Extract YAML frontmatter key-value pairs from a SKILL.md file."""
    text = skill_md.read_text()
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fields: dict = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fields[k.strip()] = v.strip().strip('"').strip("'")
    return fields


# Valid skill name: 1-64 chars, lowercase letters/numbers/hyphens,
# no leading/trailing/consecutive hyphens
SKILL_NAME_RE = re.compile(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$')


def is_valid_skill_name(name: str) -> bool:
    if not name or len(name) > 64:
        return False
    if "--" in name:
        return False
    return bool(SKILL_NAME_RE.match(name))


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_metadata(task_dir: Path, task_name: str) -> dict | None:
    """Validate metadata.json schema and cross-references."""
    meta_path = task_dir / "metadata.json"
    if not meta_path.exists():
        error("metadata.json is missing")
        return None

    meta = load_json(meta_path)
    if meta is None:
        return None

    for field in ["task_name", "category", "input_files", "test_file", "solution_file",
                  "golden_skills", "distractor_skills"]:
        if field not in meta:
            error(f"metadata.json missing required field: '{field}'")

    if meta.get("task_name") and meta["task_name"] != task_name:
        error(
            f"metadata.json task_name '{meta['task_name']}' "
            f"does not match directory name '{task_name}'"
        )

    if meta.get("test_file") and meta["test_file"] != "tests/test.py":
        error(f"metadata.json test_file must be 'tests/test.py', got: '{meta['test_file']}'")

    if meta.get("solution_file") and meta["solution_file"] != "solution/solve.sh":
        error(f"metadata.json solution_file must be 'solution/solve.sh', got: '{meta['solution_file']}'")

    golden = meta.get("golden_skills", [])
    if not isinstance(golden, list) or len(golden) == 0:
        error("metadata.json golden_skills must be a non-empty array")
    elif len(golden) > 2:
        error(f"metadata.json golden_skills has {len(golden)} items; maximum is 2")

    distractors = meta.get("distractor_skills", [])
    if not isinstance(distractors, list):
        error("metadata.json distractor_skills must be an array")
    elif len(distractors) < 3:
        error(f"metadata.json distractor_skills has {len(distractors)} items; minimum is 3")
    elif len(distractors) > 5:
        error(f"metadata.json distractor_skills has {len(distractors)} items; maximum is 5")

    if not isinstance(meta.get("input_files", []), list):
        error("metadata.json input_files must be an array")

    return meta


def check_required_files(task_dir: Path, meta: dict | None) -> None:
    """Check required top-level files and directories exist."""
    for fname in ["instruction.md", "setup.sh"]:
        if not (task_dir / fname).exists():
            error(f"{fname} is missing")

    if not (task_dir / "tests" / "test.py").exists():
        error("tests/test.py is missing")

    if not (task_dir / "solution" / "solve.sh").exists():
        error("solution/solve.sh is missing")

    input_folder = meta.get("input_files_folder", "input_files") if meta else "input_files"
    input_dir = task_dir / input_folder
    if not input_dir.exists():
        error(f"input files folder '{input_folder}' is missing")
    elif not (input_dir / ".gitkeep").exists():
        error(f"{input_folder}/.gitkeep is missing")


def check_input_files_exist(task_dir: Path, meta: dict) -> None:
    """Every file listed in metadata.json input_files must exist."""
    input_folder = meta.get("input_files_folder", "input_files")
    input_dir = task_dir / input_folder
    for fname in meta.get("input_files", []):
        if not (input_dir / fname).exists():
            error(f"input_files entry '{fname}' not found in {input_folder}/")


def check_skills(task_dir: Path, meta: dict | None) -> None:
    """Validate skills/ directory structure and SKILL.md frontmatter."""
    skills_dir = task_dir / "skills"
    if not skills_dir.exists():
        error("skills/ directory is missing")
        return

    all_declared = []
    if meta:
        all_declared = (
            list(meta.get("golden_skills", [])) +
            list(meta.get("distractor_skills", []))
        )

    for skill_name in all_declared:
        if not (skills_dir / skill_name).exists():
            error(f"skills/{skill_name}/ directory is missing (declared in metadata.json)")

    actual_skill_dirs = [d.name for d in skills_dir.iterdir() if d.is_dir()]
    for skill_name in actual_skill_dirs:
        if all_declared and skill_name not in all_declared:
            error(
                f"skills/{skill_name}/ exists but is not listed in "
                "golden_skills or distractor_skills"
            )

    for skill_name in actual_skill_dirs:
        _check_single_skill(skills_dir / skill_name, skill_name)


def _check_single_skill(skill_dir: Path, skill_name: str) -> None:
    prefix = f"skills/{skill_name}"

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        error(f"{prefix}/SKILL.md is missing")
    else:
        _check_skill_md(skill_md, skill_name, prefix)

    # scripts/ is required per the skill spec
    if not (skill_dir / "scripts").exists():
        error(f"{prefix}/scripts/ directory is missing")


def _check_skill_md(skill_md: Path, skill_name: str, prefix: str) -> None:
    """
    Validate SKILL.md frontmatter per skill spec:
    - name: required, 1-64 chars, lowercase alphanumeric + hyphens,
            no leading/trailing/consecutive hyphens, must match directory name
    - description: required, 1-1024 chars
    All other fields (license, compatibility, metadata, allowed-tools) are optional.
    """
    text = skill_md.read_text()
    fields = parse_frontmatter(skill_md)

    if not fields:
        error(f"{prefix}/SKILL.md has no valid YAML frontmatter (must start with ---)")
        return

    # --- name field ---
    name = fields.get("name", "")
    if not name:
        error(f"{prefix}/SKILL.md frontmatter missing required field: 'name'")
    else:
        if len(name) > 64:
            error(f"{prefix}/SKILL.md name is {len(name)} chars; maximum is 64")
        if not is_valid_skill_name(name):
            error(
                f"{prefix}/SKILL.md name '{name}' is invalid — "
                "must be lowercase letters, numbers, and hyphens only; "
                "no leading/trailing/consecutive hyphens"
            )
        elif name != skill_name:
            error(
                f"{prefix}/SKILL.md name '{name}' does not match "
                f"directory name '{skill_name}'"
            )

    # --- description field ---
    desc = fields.get("description", "")
    if not desc:
        error(f"{prefix}/SKILL.md frontmatter missing required field: 'description'")
    elif len(desc) > 1024:
        error(f"{prefix}/SKILL.md description is {len(desc)} chars; maximum is 1024")

    # --- size limits ---
    lines = text.splitlines()
    if len(lines) > 500:
        error(f"{prefix}/SKILL.md is {len(lines)} lines; maximum is 500")

    # Count frontmatter words
    fm_end = text.find("\n---", 3)
    if fm_end != -1:
        fm_words = len(text[3:fm_end].split())
        if fm_words > 100:
            error(f"{prefix}/SKILL.md frontmatter is {fm_words} words; maximum is 100")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def validate(task_path: Path) -> bool:
    task_name = task_path.name

    if not task_path.exists():
        error(f"Task directory does not exist: {task_path}")
        print_results(task_name)
        return False

    meta = check_metadata(task_path, task_name)
    check_required_files(task_path, meta)

    if meta:
        check_input_files_exist(task_path, meta)

    check_skills(task_path, meta)

    print_results(task_name)
    return len(errors) == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a Skills task directory")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--task-path", type=Path, help="Direct path to task directory")
    group.add_argument("--task-name", type=str, help="Task name (looked up under tasks/)")
    args = parser.parse_args()

    task_path = (
        args.task_path if args.task_path
        else Path(__file__).parent.parent / "tasks" / args.task_name
    )

    sys.exit(0 if validate(task_path) else 1)


if __name__ == "__main__":
    main()
