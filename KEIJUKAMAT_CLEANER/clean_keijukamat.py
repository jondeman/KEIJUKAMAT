#!/usr/bin/env python3
import shutil
import subprocess
import time
from pathlib import Path


KEEP_ROOT = {".git", ".github", "docs", "KEIJUKAMAT_CLEANER"}
MAX_AGE_SECONDS = 7 * 24 * 60 * 60


def _run_git(args: list[str], repo_root: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _ensure_keijukamat(repo_root: Path) -> None:
    url = _run_git(["remote", "get-url", "origin"], repo_root)
    if "KEIJUKAMAT" not in url:
        raise RuntimeError(f"Safety check failed. Origin is not KEIJUKAMAT: {url}")


def _cleanup_root(repo_root: Path) -> list[str]:
    removed: list[str] = []
    for entry in repo_root.iterdir():
        if entry.name in KEEP_ROOT:
            continue
        try:
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
            removed.append(entry.name)
        except Exception as exc:
            raise RuntimeError(f"Failed to remove {entry}: {exc}") from exc
    return removed


def _last_commit_time(repo_root: Path, file_path: Path) -> int | None:
    rel = file_path.relative_to(repo_root)
    try:
        output = _run_git(["log", "-1", "--format=%ct", "--", str(rel)], repo_root)
    except Exception:
        return None
    if not output:
        return None
    try:
        return int(output)
    except ValueError:
        return None


def _cleanup_docs(repo_root: Path) -> tuple[list[str], list[str]]:
    removed: list[str] = []
    kept: list[str] = []
    docs_dir = repo_root / "docs"
    if not docs_dir.exists():
        return removed, kept

    cutoff = int(time.time()) - MAX_AGE_SECONDS
    for path in docs_dir.rglob("*"):
        if not path.is_file():
            continue
        commit_time = _last_commit_time(repo_root, path)
        rel = str(path.relative_to(repo_root))
        if commit_time is None:
            path.unlink()
            removed.append(rel)
            continue
        if commit_time < cutoff:
            path.unlink()
            removed.append(rel)
        else:
            kept.append(rel)

    # Remove empty directories bottom-up
    dirs = sorted([p for p in docs_dir.rglob("*") if p.is_dir()], key=lambda p: len(p.parts), reverse=True)
    for d in dirs:
        try:
            d.rmdir()
        except OSError:
            pass

    return removed, kept


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _ensure_keijukamat(repo_root)

    removed_root = _cleanup_root(repo_root)
    removed_docs, kept_docs = _cleanup_docs(repo_root)

    print("KEIJUKAMAT cleaner summary")
    print(f"Removed root entries: {len(removed_root)}")
    if removed_root:
        print(" - " + ", ".join(sorted(removed_root)))
    print(f"Removed docs files: {len(removed_docs)}")
    print(f"Kept docs files: {len(kept_docs)}")


if __name__ == "__main__":
    main()
