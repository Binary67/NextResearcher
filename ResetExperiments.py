from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# === Configure this (same target repo as Main.py) ===
TARGET_REPO = "CHANGE_ME"

PROJECT_ROOT = Path(__file__).resolve().parent


def reset_experiments(target_repo: str | Path | None = None):
    worktree_count = 0
    log_count = 0
    branch_count = 0

    worktree_dir = PROJECT_ROOT / "Worktrees"
    if worktree_dir.exists():
        worktree_count = sum(1 for p in worktree_dir.iterdir() if p.is_dir())
        shutil.rmtree(worktree_dir)
        print(f"Removed {worktree_count} worktree(s) from {worktree_dir}")
    else:
        print("No worktrees to remove.")

    logs_dir = PROJECT_ROOT / "Logs"
    if logs_dir.exists():
        log_count = sum(1 for p in logs_dir.rglob("*") if p.is_file())
        shutil.rmtree(logs_dir)
        logs_dir.mkdir()
        print(f"Cleared {log_count} log file(s) from {logs_dir}")
    else:
        print("No logs to clear.")

    if target_repo and target_repo != "CHANGE_ME":
        target = Path(target_repo).resolve()
        subprocess.run(
            ["git", "-C", str(target), "worktree", "prune", "--verbose"],
            check=True,
        )
        print(f"Pruned stale worktree refs in {target}")

        deleted_branches: list[str] = []
        for pattern in ("experiment/iter_*", "best/*"):
            branch_output = subprocess.run(
                ["git", "-C", str(target), "branch", "--list", pattern],
                capture_output=True, text=True,
            ).stdout.strip()
            for line in branch_output.splitlines():
                name = line.strip().removeprefix("* ")
                if name:
                    subprocess.run(
                        ["git", "-C", str(target), "branch", "-D", name],
                        capture_output=True,
                    )
                    deleted_branches.append(name)
                    print(f"  Deleted branch: {name}")

        branch_count = len(deleted_branches)
        if branch_count:
            print(f"Deleted {branch_count} branch(es) matching experiment/iter_* and best/*")
        else:
            print("No experiment branches to delete.")

    print(f"\nReset complete. Removed {worktree_count} worktree(s), {log_count} log file(s), {branch_count} branch(es).")


reset_experiments(target_repo=TARGET_REPO)
