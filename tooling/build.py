#!/usr/bin/env python3
"""
Build the Docker environment for a downloaded GDM Skills task.

Usage:
  python3 tooling/build.py --task-name "Fix Wizard State Machine Transitions"
  python3 tooling/build.py --task-slug wizard-state-machine-fix
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path


def slugify(text: str) -> str:
    """Rough title-to-slug conversion for fuzzy matching."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def find_task_dir(task_name: str, tasks_dir: Path) -> Path | None:
    if not tasks_dir.exists():
        return None

    # 1. Exact slug match
    slug = slugify(task_name)
    direct = tasks_dir / slug
    if direct.exists():
        return direct

    # 2. Partial slug match (first 12 chars)
    candidates = [
        d for d in tasks_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
        and (slug[:12] in d.name or d.name[:12] in slug)
    ]
    if len(candidates) == 1:
        return candidates[0]

    # 3. Most-recently-modified task dir (most likely just downloaded)
    all_dirs = [
        d for d in tasks_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]
    if all_dirs:
        newest = max(all_dirs, key=lambda d: d.stat().st_mtime)
        print(f"  (using most recently modified dir: {newest.name})")
        return newest

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Build the Docker environment for a downloaded GDM Skills task."
    )
    parser.add_argument("--task-name", default=None, help="Task title (e.g. 'Fix Wizard State Machine')")
    parser.add_argument("--task-slug", default=None, help="Task directory slug (e.g. wizard-state-machine-fix)")
    args = parser.parse_args()

    if not args.task_name and not args.task_slug:
        parser.error("Provide --task-name or --task-slug")

    search_term = args.task_slug or args.task_name
    tasks_dir = Path(__file__).parent.parent / "tasks"
    task_dir = find_task_dir(search_term, tasks_dir)

    if task_dir is None:
        print(f"ERROR: No task directory found in tasks/ matching '{search_term}'")
        print()
        print("  Have you downloaded the task yet? Run:")
        print("    python3 tooling/download_s3.py --s3-url <presigned-url>")
        sys.exit(1)

    task_slug = task_dir.name
    env_dir = task_dir / "environment"
    dockerfile = env_dir / "Dockerfile"

    if not dockerfile.exists():
        print(f"No Dockerfile found in {env_dir}")
        print("This task may not use a Docker environment.")
        sys.exit(0)

    print(f"Building Docker image: {task_slug}")
    print(f"  From: {env_dir.relative_to(Path.cwd())}")
    print()

    result = subprocess.run(
        ["docker", "build", "--platform", "linux/amd64", "-t", task_slug, str(env_dir)],
        check=False,
    )

    if result.returncode != 0:
        print(f"\nDocker build failed (exit {result.returncode})")
        sys.exit(result.returncode)

    print(f"\n✓ Image built: {task_slug}")
    print()
    print("━" * 60)
    print("Next steps:")
    print()
    print(f"  # Run the container interactively:")
    print(f"  docker run --rm -it {task_slug} bash")
    print()
    print(f"  # Read the task instructions inside the container:")
    print(f"  docker run --rm {task_slug} cat /app/instruction.md")
    print()
    print(f"  # Edit your solution:")
    print(f"  # tasks/{task_slug}/solution/solve.sh")
    print()
    print(f"  # Test your solution:")
    print(f"  docker run --rm \\")
    print(f"    -v \"$(pwd)/tasks/{task_slug}/solution:/solution\" \\")
    print(f"    {task_slug} bash -c 'bash /solution/solve.sh'")
    print("━" * 60)


if __name__ == "__main__":
    main()
