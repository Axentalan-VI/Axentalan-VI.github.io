"""Fetch best public leaderboard scores from the owner's Kaggle submissions.

Outcomes on the site must be verifiable, not asserted. This pulls them from
the submission history via the Kaggle CLI and prints a table to paste into
projects.json. It writes nothing automatically - scores need human judgement
about whether a single early submission is worth showing at all.

Usage:
    KAGGLE_CONFIG_DIR=E:/Kaggle PYTHONUTF8=1 python scripts/fetch_scores.py

Note: the CLI takes roughly 10-20 seconds per competition, so the full sweep
runs for several minutes. That is the CLI, not a hang.
"""
import csv
import io
import json
import pathlib
import subprocess
import sys

SITE = pathlib.Path(__file__).resolve().parent.parent
KAGGLE = "kaggle"  # on PATH via E:\miniconda\Scripts

# Every metric listed here is higher-is-better. Add a competition to
# LOWER_IS_BETTER if that ever stops being true, or the "best" will be wrong.
LOWER_IS_BETTER = set()


def competition_slug(url):
    return url.rstrip("/").rsplit("/", 1)[-1] if url else None


class KaggleUnavailable(Exception):
    """The Kaggle CLI could not be run at all."""


def best_score(slug):
    """Return (best, completed_count) from the submission history."""
    try:
        result = subprocess.run(
            [KAGGLE, "competitions", "submissions", "-c", slug, "--csv"],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except (FileNotFoundError, OSError) as error:
        # Raised when the kaggle CLI is not on PATH. This script is run by hand
        # from whatever shell is open, so this is the common failure, and a
        # stack trace tells the reader nothing about how to fix it.
        raise KaggleUnavailable(str(error)) from error
    if result.returncode != 0:
        return None, "error"

    rows = list(csv.DictReader(io.StringIO(result.stdout)))
    completed = [r for r in rows if "COMPLETE" in (r.get("status") or "")]
    scores = []
    for row in completed:
        raw = (row.get("publicScore") or "").strip()
        if not raw:
            continue
        try:
            scores.append(float(raw))
        except ValueError:
            pass
    if not scores:
        return None, len(completed)
    best = min(scores) if slug in LOWER_IS_BETTER else max(scores)
    return best, len(completed)


def main():
    projects = json.loads(
        (SITE / "data" / "projects.json").read_text(encoding="utf-8")
    )
    print(f"{'id':<22} {'best':>12} {'subs':>6}  {'on site':>12}")
    print("-" * 58)
    for project in projects:
        slug = competition_slug(project.get("competition"))
        on_site = (project.get("outcome") or {}).get("value", "-")
        if not slug:
            print(f"{project['id']:<22} {'(no comp)':>12} {'-':>6}  {on_site:>12}")
            continue
        try:
            best, count = best_score(slug)
        except KaggleUnavailable as error:
            print()
            print("Could not run the Kaggle CLI, so no scores were fetched.")
            print(f"  reason: {error}")
            print()
            print("The CLI is installed but may not be on this shell's PATH.")
            print("On this machine it lives in E:\\miniconda\\Scripts, so run:")
            print()
            print('  KAGGLE_CONFIG_DIR=E:/Kaggle PYTHONUTF8=1 \\')
            print('    PATH="/e/miniconda/Scripts:$PATH" \\')
            print("    python scripts/fetch_scores.py")
            print()
            print("Credentials are read from kaggle.json in KAGGLE_CONFIG_DIR;")
            print("do not pass the key on the command line.")
            return 2
        shown = "-" if best is None else f"{best:g}"
        print(f"{project['id']:<22} {shown:>12} {str(count):>6}  {on_site:>12}")
    print("\nCompare 'best' against 'on site'; any drift means projects.json "
          "is stale.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
