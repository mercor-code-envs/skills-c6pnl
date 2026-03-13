# Skills — Expert Task Creation Guide

Each task in this dataset is a software engineering problem that frontier models **fail without a custom skill** but can solve with it. Your job is to create one such task.

---

## Quick Start

1. Fork this repo
2. Create a new directory under `tasks/` named after your task (kebab-case, e.g. `parse-jwt-expiry-edge-case`)
3. Use `example_tasks/jwt-claims-validator/` as a reference for structure and conventions
4. Run locally to verify: `bash tasks/<your-task>/setup.sh && python tasks/<your-task>/tests/test.py`
5. Open a PR for review

---

## Task Directory Structure

```
<task-name>/
├── metadata.json            # Task config: skills, failure modes, file refs
├── instruction.md           # The prompt the model receives (no skill hints)
├── setup.sh                 # All apt/pip installs + env setup
├── input_files/             # Files placed in /app/ at runtime
│   └── .gitkeep             # Keep even if empty
├── tests/
│   └── test.py              # Single verifier — must print "pass" or "fail" to stdout
├── skills/
│   ├── <golden-skill>/
│   │   ├── SKILL.md         # Skill document: when to use, approach, edge cases, scripts
│   │   └── scripts/         # Helper scripts + unit tests
│   ├── <distractor-1>/
│   │   ├── SKILL.md
│   │   └── scripts/
│   └── ...                  # 3–5 distractors total
├── solution/
│   └── solve.sh             # Oracle solution — must make test.py pass
└── trajectories/
    └── .gitkeep             # Client populates this; leave empty
```

---

## File-by-File Guide

### `metadata.json`

```json
{
  "task_name": "your-task-name",
  "category": "Descriptive category string, e.g. Authentication & Security, Systems Programming, ML / Distributed Computing",
  "input_files": ["file1.py", "file2.json"],
  "test_file": "tests/test.py",
  "solution_file": "solution/solve.sh",
  "golden_skills": ["golden-skill-name"],
  "distractor_skills": ["distractor-1", "distractor-2", "distractor-3", "distractor-4"]
}
```

**Notes:**
- `task_name` must match the directory name exactly
- `golden_skills` is an array — include all golden skills (most tasks have 1–2)
- Each skill name in `golden_skills` and `distractor_skills` must match the corresponding directory name under `skills/` exactly

---

### `instruction.md`

The prompt the model receives. Rules:
- Describe the problem clearly — what exists at `/app`, what output is expected
- **No hints** about which skill to use or how to approach the problem
- Do not reference the golden skill by name or concept
- Self-contained: a model with no context should understand the task from this alone

---

### `setup.sh`

```bash
#!/bin/bash
set -e

# System packages
apt-get update && apt-get install -y \
    <package1> \
    <package2>

# Python packages
pip install \
    <package1> \
    <package2>
```

- All dependencies that `test.py` or `solve.sh` need must be installed here
- Even if no setup is needed, this file must exist (leave it as `#!/bin/bash` with `set -e`)
- Do **not** include any logic that should be in `solve.sh`

---

### `tests/test.py`

- Single pytest entrypoint
- Must print `pass` to stdout on success, `fail` on failure
- Do not test the skill itself — test the task's oracle outcome
- Verifier must be deterministic; avoid timing-based checks

Pattern:
```python
import pytest
import sys

def test_main():
    # ... your assertions ...
    pass

if __name__ == "__main__":
    result = pytest.main([__file__, "-v"])
    print("pass" if result == 0 else "fail")
```

---

### `skills/<skill-name>/SKILL.md`

```markdown
---
name: skill-name
description: "One sentence: when to use this skill and what it covers."
---

# Skill Title

## When to use

Describe the trigger condition precisely — what kind of task or problem should cause the model to select this skill.

## Approach

Step-by-step guidance for how to apply the skill. Be concrete and actionable.

## Edge cases

Common failure patterns and how to handle them.

## Scripts

- `scripts/helper.py` — What it does, usage: `python helper.py <args>`
- `scripts/test_helper.py` — Unit test; run with `python test_helper.py`
```

**Golden skill rules:**
- General-purpose: must be useful beyond just this one task
- Not a solution guide: don't describe how to solve the specific task
- Minimal wording overlap with `instruction.md`
- Scripts must have passing unit tests

**Distractor skill rules:**
- Cosine similarity ≥ 0.6 with the golden skill on both name and description
- Must pass the same SKILL.md formatting requirements as the golden skill
- Must be plausible — a model should reasonably consider them relevant

---

### `solution/solve.sh`

The oracle solution. Must:
- Run without errors after `setup.sh` has executed
- Cause `python tests/test.py` to print `pass`

---

## Difficulty Bar

Your task must satisfy both conditions:

| Condition | Requirement |
|-----------|-------------|
| Without skill | Model **fails** (reward = 0) |
| With golden skill | Model **passes** and triggers the golden skill **autonomously** (no explicit skill nudge in the prompt) |

If the model passes without the skill, the task is too easy — make it harder.
If the model fails even with the skill, the skill needs more detail or the task needs adjustment.

---

## Local Verification Checklist

Before opening a PR:

- [ ] `bash tasks/<task-name>/setup.sh` exits 0
- [ ] `python tasks/<task-name>/tests/test.py` prints `pass`
- [ ] `bash tasks/<task-name>/solution/solve.sh && python tasks/<task-name>/tests/test.py` prints `pass`
- [ ] `python tasks/<task-name>/skills/<skill>/scripts/test_*.py` passes for all skills
- [ ] `metadata.json` is valid JSON and all referenced files exist
- [ ] `instruction.md` contains no skill hints
- [ ] Golden skill is general-purpose (not task-specific)
- [ ] 3–5 distractor skills present with passing unit tests
