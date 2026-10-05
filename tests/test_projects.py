"""Schema and selection rules for projects.json."""
import json
import pathlib
import re

import pytest

SITE = pathlib.Path(__file__).resolve().parent.parent
PROJECTS = json.loads((SITE / "data" / "projects.json").read_text(encoding="utf-8"))

REQUIRED = {"id", "title", "track", "featured", "problem", "approach",
            "constraint", "tags", "status", "repo", "competition", "outcome"}
TRACKS = {"ml", "agents"}
STATUSES = {"in-progress", "submitted", "completed"}


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p["id"])
def test_project_has_exact_fields(project):
    assert set(project) == REQUIRED, (
        f"{project['id']}: field mismatch, "
        f"missing={REQUIRED - set(project)}, extra={set(project) - REQUIRED}"
    )


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p["id"])
def test_project_field_values(project):
    assert project["track"] in TRACKS
    assert project["status"] in STATUSES
    assert isinstance(project["featured"], bool)
    assert isinstance(project["tags"], list) and project["tags"]
    assert project["problem"].endswith("."), "problem should be a sentence"
    for url in (project["repo"], project["competition"]):
        assert url is None or url.startswith("https://"), (
            "URLs must be absolute https, or null for no link"
        )


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p["id"])
def test_featured_projects_have_approach_bullets(project):
    if project["featured"]:
        assert 2 <= len(project["approach"]) <= 3, (
            "featured cards render 2-3 approach bullets"
        )
    else:
        assert project["approach"] == [], (
            "compact cards render problem and tags only"
        )


def test_ids_are_unique():
    ids = [p["id"] for p in PROJECTS]
    assert len(ids) == len(set(ids))


def test_featured_selection():
    featured = [p for p in PROJECTS if p["featured"]]
    assert len(featured) == 6
    ml = [p for p in featured if p["track"] == "ml"]
    agents = [p for p in featured if p["track"] == "agents"]
    assert len(ml) == 3, "three featured applied-ML projects"
    assert len(agents) == 3, "three featured agent projects"


def test_amia_repo_link_is_correct_when_present():
    """AMIA's repo is private while its competition runs, so the link is null.

    If it is ever made public again the link must be the real URL, not a
    guess - so assert the value rather than merely its absence.
    """
    amia = next(p for p in PROJECTS if p["id"] == "amia-2026")
    assert amia["repo"] in (
        None, "https://github.com/Axentalan-VI/amia-public-challenge-2026"
    )


def test_no_scores_claimed():
    """No competition score, rank or placement may appear in project copy.

    Word-boundary regexes, not substrings: a bare "rank " substring would
    falsely flag legitimate technical copy such as "max_lora_rank 32".
    """
    banned = [
        r"\btop\s+\d+\s*%",
        r"\brank(?:ed)?\s+#?\d",
        r"\bleaderboard\b",
        r"\b(?:bronze|silver|gold)\s+medal\b",
        r"\bcv\s+(?:score|of)\b",
        r"\b(?:public|private)\s+lb\b",
        r"\bplaced\s+\d",
    ]
    for project in PROJECTS:
        blob = " ".join([
            project["problem"], project["constraint"] or "", *project["approach"]
        ]).lower()
        for pattern in banned:
            match = re.search(pattern, blob)
            assert not match, (
                f"{project['id']}: unverified claim {match.group(0)!r} "
                f"in project copy"
            )


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p["id"])
def test_outcome_shape(project):
    outcome = project["outcome"]
    if outcome is None:
        return
    assert set(outcome) == {"value", "metric", "context", "submissions"}, (
        f"{project['id']}: outcome field mismatch"
    )
    assert isinstance(outcome["value"], str) and outcome["value"]
    assert isinstance(outcome["metric"], str) and outcome["metric"]
    assert isinstance(outcome["submissions"], int)
    assert outcome["submissions"] >= 1, (
        "an outcome must come from at least one completed submission"
    )


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p["id"])
def test_outcome_requires_a_competition(project):
    """A leaderboard score cannot exist without a leaderboard."""
    if project["outcome"] is not None:
        assert project["competition"], (
            f"{project['id']}: outcome claimed with no competition link to "
            f"verify it against"
        )


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p["id"])
def test_single_submission_outcomes_say_so(project):
    """One submission is a probe, not a result. The copy must admit it."""
    outcome = project["outcome"]
    if outcome and outcome["submissions"] == 1:
        assert "first submission" in outcome["context"].lower(), (
            f"{project['id']}: a single-submission score must be labelled "
            f"as a first submission"
        )
