from __future__ import annotations

import shutil
import subprocess
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "CodexConfig.toml"
BEST_STATE_PATH = PROJECT_ROOT / "BestState.json"

config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
TARGET_REPO = config["Experiment"]["target_repo"]


def reset_experiments(target_repo: str | Path | None = None):
    worktree_count = 0
    log_count = 0
    branch_count = 0
    metadata_removed = False

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

    if BEST_STATE_PATH.exists():
        BEST_STATE_PATH.unlink()
        metadata_removed = True
        print(f"Removed best state metadata: {BEST_STATE_PATH}")
    else:
        print("No best state metadata to remove.")

    if target_repo:
        target = Path(target_repo).resolve()
        subprocess.run(
            ["git", "-C", str(target), "worktree", "prune", "--verbose"],
            check=True,
        )
        print(f"Pruned stale worktree refs in {target}")

        deleted_branches: list[str] = []
        for pattern in ("experiment/iter_*", "best/*"):
            branch_output = subprocess.run(
                ["git", "-C", str(target), "branch", "--format=%(refname:short)", "--list", pattern],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            for name in [line.strip() for line in branch_output.splitlines() if line.strip()]:
                delete_result = subprocess.run(
                    ["git", "-C", str(target), "branch", "-D", name],
                    capture_output=True,
                    text=True,
                )
                if delete_result.returncode == 0:
                    deleted_branches.append(name)
                    print(f"  Deleted branch: {name}")
                else:
                    stderr = delete_result.stderr.strip() or "unknown error"
                    print(f"  Warning: failed to delete branch {name}: {stderr}")

        branch_count = len(deleted_branches)
        if branch_count:
            print(f"Deleted {branch_count} branch(es) matching experiment/iter_* and best/*")
        else:
            print("No experiment branches to delete.")

    metadata_count = 1 if metadata_removed else 0
    print(
        f"\nReset complete. Removed {worktree_count} worktree(s), {log_count} log file(s), "
        f"{branch_count} branch(es), {metadata_count} metadata file(s)."
    )


reset_experiments(target_repo=TARGET_REPO)
