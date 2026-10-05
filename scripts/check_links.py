"""Verify every outbound URL on the site resolves.

A broken link on a portfolio is the classic own-goal: the repo names here are
long and easy to mistype. Run before every push.

Usage:  python scripts/check_links.py
Exits non-zero if any URL fails.
"""
import json
import pathlib
import sys
import urllib.error
import urllib.request

SITE = pathlib.Path(__file__).resolve().parent.parent
TIMEOUT = 20
USER_AGENT = "portfolio-link-check/1.0"


def collect_urls():
    """Yield (source, url) for every external URL in the data files."""
    profile = json.loads((SITE / "data" / "profile.json").read_text(encoding="utf-8"))
    for item in profile["links"]:
        if item["url"].startswith("http"):
            yield f"profile:{item['label']}", item["url"]

    projects = json.loads((SITE / "data" / "projects.json").read_text(encoding="utf-8"))
    for project in projects:
        for field in ("repo", "competition"):
            if project[field]:
                yield f"{project['id']}:{field}", project[field]


def check(url):
    """Return (ok, detail). Treats any 2xx/3xx as reachable."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return 200 <= response.status < 400, str(response.status)
    except urllib.error.HTTPError as error:
        # Some sites refuse unauthenticated clients without the page being
        # missing: Kaggle answers 403 for certain competition pages, and
        # LinkedIn answers 999 to anything it thinks is a bot. Neither means
        # the link is broken, and a checker that cried wolf on them would be
        # ignored within a week.
        if error.code == 403:
            return True, "403 (exists, auth required)"
        if error.code == 999:
            return True, "999 (LinkedIn bot block)"
        return False, f"HTTP {error.code}"
    except Exception as error:  # network, DNS, TLS
        return False, f"{type(error).__name__}: {error}"


def main():
    failures = []
    for source, url in collect_urls():
        ok, detail = check(url)
        print(f"{'OK  ' if ok else 'FAIL'}  {detail:<26} {source:<28} {url}")
        if not ok:
            failures.append((source, url, detail))

    print()
    if failures:
        print(f"{len(failures)} broken link(s):")
        for source, url, detail in failures:
            print(f"  {source}: {url} - {detail}")
        return 1
    print("All links OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
