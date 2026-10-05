"""Guards on app.js behaviour that is invisible when broken."""
import pathlib
import re

SITE = pathlib.Path(__file__).resolve().parent.parent
APP = (SITE / "assets" / "app.js").read_text(encoding="utf-8")
HTML = (SITE / "index.html").read_text(encoding="utf-8")


def test_null_repo_renders_no_link():
    """A project with repo: null must produce no anchor at all."""
    assert "function linkOrNothing" in APP, (
        "expected a helper that returns an empty string for a null URL"
    )
    body = APP.split("function linkOrNothing")[1].split("\n}")[0]
    assert re.search(r"if\s*\(\s*!url\s*\)\s*return\s*['\"]{2}", body), (
        "linkOrNothing must return an empty string when url is falsy"
    )


def test_escape_helper_exists_and_covers_all_entities():
    assert "function escapeHtml" in APP
    body = APP.split("function escapeHtml")[1].split("\n}")[0]
    for entity in ("&amp;", "&lt;", "&gt;", "&quot;"):
        assert entity in body, f"escapeHtml must handle {entity}"


def test_all_interpolated_values_are_escaped():
    """No raw JSON value may reach innerHTML unescaped."""
    raw = re.findall(r"\$\{\s*(?!escapeHtml|linkOrNothing|tagList|bulletList)"
                     r"(p|item|entry|group)\.\w+", APP)
    assert not raw, f"unescaped interpolations into markup: {raw}"


def test_fetch_failure_renders_fallback():
    assert "catch" in APP, "the JSON fetch must be wrapped in try/catch"
    assert "github.com/Axentalan-VI" in APP, (
        "the fallback message must point at the GitHub profile"
    )


def test_filter_defaults_to_all():
    assert 'data-track="all"' in HTML
    assert re.search(r'data-track="all"[^>]*class="[^"]*\bis-active\b', HTML) or \
           re.search(r'class="[^"]*\bis-active\b[^"]*"[^>]*data-track="all"', HTML), (
        "the All filter button must start active"
    )


def test_mount_points_exist():
    for mount in ("profile-text", "experience", "featured", "compact",
                  "skills", "education", "certifications", "link-row"):
        assert f'id="{mount}"' in HTML, f"missing mount point #{mount}"


def test_html_declares_viewport_and_title():
    assert 'name="viewport"' in HTML
    assert "Ahmed Elfiky" in HTML


def test_fetch_paths_are_relative():
    """A leading slash breaks the fetch on a project-page deployment.

    GitHub Pages serves a user site from the domain root, but a repo renamed or
    moved under a path would serve from a subdirectory; a relative path works in
    both cases, an absolute one only in the first.
    """
    absolute = re.findall(r'fetch\(\s*["\']/', APP)
    assert not absolute, (
        "fetch() paths must be relative (data/...), not absolute (/data/...)"
    )


def test_referenced_assets_exist_on_disk():
    """Every file index.html points at must actually be in the repo."""
    refs = re.findall(r'(?:href|src)="(?!https?:|mailto:|#)([^"]+)"', HTML)
    missing = [ref for ref in refs if not (SITE / ref).exists()]
    assert not missing, f"index.html references missing files: {missing}"
