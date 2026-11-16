"""Every skill folder is well-formed and the getting-started registry matches them."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
REGISTRY = SKILLS / "sl-ramis-getting-started" / "references" / "skills-registry.md"


def frontmatter(path):
    m = re.match(r"^---\n(.*?)\n---\n", path.read_text(), re.S)
    assert m, "%s has no front-matter" % path
    return dict(re.findall(r"^(\w+):\s*(.+)$", m.group(1), re.M))


def test_every_skill_has_matching_frontmatter():
    dirs = [d for d in SKILLS.iterdir() if d.is_dir()]
    assert dirs
    for d in dirs:
        fm = frontmatter(d / "SKILL.md")
        assert fm.get("name") == d.name
        assert len(fm.get("description", "")) > 50


def test_registry_matches_installed_skills():
    rows = re.findall(r"^\|\s*\d+\s*\|\s*`([\w-]+)`\s*\|\s*\**(\w+)\**\s*\|", REGISTRY.read_text(), re.M)
    assert rows
    present = {d.name for d in SKILLS.iterdir() if d.is_dir()}
    for name, status in rows:
        if status == "available":
            assert name in present, "%s listed as available but missing" % name
        else:
            assert status == "planned"
    listed = {n for n, _ in rows}
    assert present - listed == {"sl-ramis-getting-started"}, "filing skill missing from registry"
