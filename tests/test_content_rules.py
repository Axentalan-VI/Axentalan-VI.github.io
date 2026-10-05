"""Content rules that must hold across the whole published site.

NOTE ON SCOPE: the checks for forbidden literals — the owner's phone number,
employer-internal URLs, excluded projects, AI-attribution strings — deliberately
do NOT live here. This file is committed to the public repo, so naming those
strings would publish the very text they exist to keep out, and the tests would
fail against their own source. Those checks run from
`Portfolio/scripts/check_forbidden.py`, which stays in the private working repo
and is executed before every push.

What remains here are the rules that can be stated without naming forbidden
text: the profile data is complete and internally correct, the CV is present,
and no placeholder copy survived.
"""
import json
import pathlib

SITE = pathlib.Path(__file__).resolve().parent.parent

TEXT_SUFFIXES = {".html", ".css", ".js", ".json", ".md", ".py", ""}


def site_text_files():
    """Every text file in the site, excluding VCS and cache directories."""
    skip = {".git", "__pycache__", ".pytest_cache"}
    for path in SITE.rglob("*"):
        if not path.is_file():
            continue
        if skip & set(path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        yield path


def test_no_placeholder_text():
    placeholders = ["lorem ipsum", "TODO:", "TBD"]
    hits = []
    for path in site_text_files():
        if path.name == "test_content_rules.py":
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for token in placeholders:
            if token.lower() in content.lower():
                hits.append(f"{path.relative_to(SITE)}: {token}")
    assert not hits, f"placeholder text left in the site: {hits}"


def test_profile_json_is_valid_and_complete():
    data = json.loads((SITE / "data" / "profile.json").read_text(encoding="utf-8"))
    for key in ("identity", "links", "profile", "experience", "skills",
                "education", "certifications"):
        assert key in data, f"profile.json missing {key!r}"

    identity = data["identity"]
    assert identity["name"] == "Ahmed Elfiky"
    assert identity["title"] == "AI Engineer"
    assert identity["location"] == "Giza, Egypt"

    assert len(data["experience"]) == 2
    palm = data["experience"][0]
    assert palm["organization"] == "Palm Hills Developments"
    assert len(palm["bullets"]) == 6

    certs = " ".join(data["certifications"])
    assert "Azure AI Apps and Agents Developer Associate, 2027" in certs
    assert "AI-102" not in certs


def test_every_link_is_absolute_or_a_local_asset():
    """A link that is neither absolute nor a file in this repo is a dead link."""
    data = json.loads((SITE / "data" / "profile.json").read_text(encoding="utf-8"))
    for item in data["links"]:
        url = item["url"]
        if url.startswith(("http://", "https://", "mailto:")):
            continue
        assert (SITE / url).exists(), (
            f"relative link {url!r} ({item['label']}) points at no file"
        )


def test_cv_pdf_is_present():
    pdf = SITE / "assets" / "Ahmed_Elfiky_AI_Engineer.pdf"
    assert pdf.exists(), "CV PDF missing from assets/"
    assert pdf.stat().st_size > 100_000, "CV PDF looks truncated"
