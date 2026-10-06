"""fetch_scores.py must fail helpfully, not with a traceback.

It is run by hand, from whatever shell the owner happens to be in, months
apart. The two things that go wrong are the Kaggle CLI not being on PATH and
credentials not being configured; neither should produce a stack trace.
"""
import pathlib
import subprocess
import sys

SITE = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = SITE / "scripts" / "fetch_scores.py"


def run(env_path):
    env = {"PATH": env_path, "SYSTEMROOT": "C:\\Windows"}
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True, timeout=300, cwd=str(SITE), env=env,
    )


def test_missing_kaggle_cli_explains_itself_instead_of_crashing():
    """PATH without the Kaggle CLI on it."""
    result = run("C:\\Windows\\System32")
    combined = result.stdout + result.stderr
    assert "Traceback" not in combined, (
        f"raw traceback shown to the user:\n{combined}"
    )
    assert "kaggle" in combined.lower(), (
        "the message should name the Kaggle CLI as the missing piece"
    )
    assert result.returncode != 0, "a failed run must not report success"
