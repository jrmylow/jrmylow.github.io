"""Content for the designed build: hand-picked cases as data, plus generated filler.

The designed build replaces docs/_posts and docs/_previews with this, so tests can
rely on cases the real corpus may never contain. Tests take expectations from this
spec and URLs from the build's manifest (see sites.py).

Filler is for scale runs (`--scale-posts=N`): generated posts, all dated before the
designed cases, so newest-first pages (home, /essays/) still show the designed cases.
"""

import datetime as dt
import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml

FIXTURE_PREVIEWS = Path(__file__).resolve().parent / "fixtures" / "_previews"


@dataclass(frozen=True)
class Post:
    date: dt.date
    slug: str
    title: str
    tags: tuple[str, ...] = ()
    body: str = "A designed post."

    @property
    def filename(self) -> str:
        return f"{self.date.isoformat()}-{self.slug}.md"

    def render(self) -> str:
        front = {"layout": "post", "title": self.title, "date": self.date, "tags": list(self.tags)}
        return f"---\n{yaml.safe_dump(front, sort_keys=False, allow_unicode=True)}---\n\n{self.body}\n"


# Hand-picked cases, newest first. P2 grows this list; say what each case is for.
DESIGNED = [
    # Tag sets where AND and OR filtering differ: A only, B only, both.
    Post(dt.date(2025, 3, 1), "designed-alpha", "Designed alpha", ("alpha",)),
    Post(dt.date(2025, 2, 1), "designed-beta", "Designed beta", ("beta",)),
    Post(dt.date(2025, 1, 1), "designed-alpha-beta", "Designed alpha and beta", ("alpha", "beta")),
]

FILLER_TAGS = ("systems", "planning", "writing", "tools", "notes")
FILLER_WORDS = 300
_VOCABULARY = (
    "the archive grows by one essay at a time and each essay adds a card a tag and a search entry "
    "so every page that lists essays has more to render and every index has more to carry"
).split()


def _filler(i: int, date: dt.date) -> Post:
    """Filler post i: a unique token for search, one or two tags from a small pool, ~300 words."""
    words = " ".join(_VOCABULARY[(i + k) % len(_VOCABULARY)] for k in range(FILLER_WORDS))
    tags = (FILLER_TAGS[i % 5],) if i % 3 else (FILLER_TAGS[i % 5], FILLER_TAGS[(i + 1) % 5])
    return Post(date, f"filler-{i:05d}", f"Filler {i:05d}", tags, f"Filler post {i:05d}, token filler{i:05d}. {words}.")


def posts(total: int | None = None) -> list[Post]:
    """The designed cases, plus filler up to `total` posts."""
    if total is None:
        return list(DESIGNED)
    if total < len(DESIGNED):
        raise ValueError(f"--scale-posts must be at least {len(DESIGNED)}, the designed cases; got {total}")
    oldest = min(post.date for post in DESIGNED)
    return DESIGNED + [_filler(i, oldest - dt.timedelta(days=i + 1)) for i in range(total - len(DESIGNED))]


def preview_files() -> list[str]:
    """File names of the fixture previews, which live in _tests/fixtures/_previews/."""
    return sorted(path.name for path in FIXTURE_PREVIEWS.glob("*.md"))


def write(src: Path, total: int | None = None) -> None:
    """Write the corpus into a copy of docs/ that has no _posts or _previews of its own."""
    posts_dir = src / "_posts"
    posts_dir.mkdir()
    for post in posts(total):
        (posts_dir / post.filename).write_text(post.render(), encoding="utf-8")
    shutil.copytree(FIXTURE_PREVIEWS, src / "_previews")
