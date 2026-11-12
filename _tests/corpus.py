"""Content for the designed build: hand-picked cases as data, plus generated filler.

The designed build replaces docs/_posts and docs/_previews with this, so tests can
rely on cases the real corpus may never contain. Tests take expectations from this
spec and URLs from the build's manifest (see sites.py).

Filler is for scale runs (`--scale-posts=N`): generated posts, all dated before the
designed cases, so newest-first pages (home, /essays/) still show the designed cases.
"""

import dataclasses
import datetime as dt
import shutil
from pathlib import Path

import yaml

FIXTURE_PREVIEWS = Path(__file__).resolve().parent / "fixtures" / "_previews"


@dataclasses.dataclass(frozen=True)
class Post:
    date: dt.date
    slug: str
    title: str
    tags: tuple[str, ...] = ()
    body: str = "A designed post."
    summary: str | None = None  # front-matter summary; None leaves cards and the feed to the excerpt
    series: str | None = None
    series_order: int | None = None

    @property
    def filename(self) -> str:
        return f"{self.date.isoformat()}-{self.slug}.md"

    @property
    def permalink(self) -> str:
        """The URL an author would type to link here. Tests take URLs from the build's manifest."""
        return f"/{self.date:%Y/%m/%d}/{self.slug}/"

    def render(self) -> str:
        front = {"layout": "post", "title": self.title, "date": self.date, "tags": list(self.tags)}
        if self.summary is not None:
            front["summary"] = [{"p": self.summary}]
        if self.series is not None:
            front["series"] = self.series
            front["series_order"] = self.series_order
        return f"---\n{yaml.safe_dump(front, sort_keys=False, allow_unicode=True)}---\n\n{self.body}\n"


# Each case below is named for the one thing it is there to show. Dates are spread so that
# "newest first" is a different order from the order the cases are listed in any other way.

# Tags: alpha is on four posts and beta on two, so a count read from the wrong tag shows, and
# every way of combining them selects a different set: alpha 4, beta 2, both 1, either 5.
# ALPHA_BETA is also the only 2024 post, so the year-grouped archive has more than one year.
ALPHA = Post(dt.date(2025, 3, 1), "designed-alpha", "Designed alpha", ("alpha",))
# Second newest, so it has a card on the home and essays pages; its summary is not its body.
ALPHA_TWO = Post(
    dt.date(2025, 2, 20),
    "designed-alpha-two",
    "Designed alpha two",
    ("alpha",),
    summary="The summary of alpha two, which its body does not contain.",
)
BETA = Post(dt.date(2025, 2, 1), "designed-beta", "Designed beta", ("beta",))
ALPHA_THREE = Post(dt.date(2025, 1, 10), "designed-alpha-three", "Designed alpha three", ("alpha",))
ALPHA_BETA = Post(dt.date(2024, 12, 1), "designed-alpha-beta", "Designed alpha and beta", ("alpha", "beta"))

# Tags no other post has. "alphabet" contains "alpha", so matching tags by substring shows.
# "quokka" is in no title and no body, so only a search of the tags themselves finds it.
UNSHARED_TAGS = Post(dt.date(2025, 1, 28), "designed-unshared-tags", "Designed unshared tags", ("alphabet", "quokka"))

# Links between posts, for "Referenced by". LINKED has one linker newer than it and one older,
# and LINKS_OUT also links to itself, which must not make it its own reference.
# All of these are dated behind the newest six, to keep them off the home and essays pages:
# a card whose first paragraph holds a link is broken (a known bug; see test_cards.py).
LINKED = Post(dt.date(2025, 1, 13), "designed-linked", "Designed linked")
_links_out = Post(dt.date(2025, 1, 16), "designed-links-out", "Designed links out")
LINKS_OUT = dataclasses.replace(
    _links_out,
    body=f"Links to [the linked post]({LINKED.permalink}) and to [itself]({_links_out.permalink}).",
)
LINKS_OUT_TWO = Post(
    dt.date(2025, 1, 11),
    "designed-links-out-two",
    "Designed links out two",
    (),
    f"Also links to [the linked post]({LINKED.permalink}).",
)

# The same, with the link written as Jekyll's post_url tag by a newer post. See test_backlinks.
LIQUID_LINKED = Post(dt.date(2025, 1, 12), "designed-liquid-linked", "Designed Liquid linked")
LIQUID_LINKS_OUT = Post(
    dt.date(2025, 1, 14),
    "designed-liquid-links-out",
    "Designed Liquid links out",
    (),
    f"Links to [the Liquid-linked post]({{% post_url {LIQUID_LINKED.filename.removesuffix('.md')} %}}).",
)

# A series whose order is neither date order: by date the parts run second, first, third.
SERIES = "Designed series"
SERIES_THIRD = Post(
    dt.date(2025, 1, 22), "designed-series-third", "Designed series third", series=SERIES, series_order=3
)
SERIES_FIRST = Post(
    dt.date(2025, 1, 21), "designed-series-first", "Designed series first", series=SERIES, series_order=1
)
SERIES_SECOND = Post(
    dt.date(2025, 1, 20), "designed-series-second", "Designed series second", series=SERIES, series_order=2
)
# A series of one, which gets no series navigation.
SERIES_SOLO = Post(
    dt.date(2025, 1, 18), "designed-series-solo", "Designed series solo", series="Designed solo series", series_order=1
)

# A title holding markup. Search results must show it as text, never as an element.
MARKUP_TITLE = Post(dt.date(2025, 1, 25), "designed-markup-title", "Designed <i>markup</i> title")

# Text that each output context must escape its own way. Unescaped, "&" and "<" make the feed
# malformed XML, and in a mailto: subject "&" ends the subject while a "+" for the space shows
# as a plus. Its summary differs from its body, so "the summary wins over the excerpt" shows.
ESCAPING_POST = Post(
    dt.date(2025, 1, 15),
    "designed-escaping",
    "Designed R&D: a < b",
    (),
    "Escaping body, R&D: a < b.",
    "Escaping summary, R&D: a < b.",
)

# Reading time: a long body whose minutes round up, against the one-line bodies above.
# 1000 words / 220 wpm is about 4.5 minutes, which rounds up to 5.
# Second newest, so it has a card on the home and essays pages.
LONG_WORDS = 1000
LONG_POST = Post(dt.date(2025, 2, 25), "designed-long", "Designed long", (), " ".join(["word"] * LONG_WORDS))

# Newest first, the order Jekyll lists posts in.
DESIGNED = [
    ALPHA,
    LONG_POST,
    ALPHA_TWO,
    BETA,
    UNSHARED_TAGS,
    MARKUP_TITLE,
    SERIES_THIRD,
    SERIES_FIRST,
    SERIES_SECOND,
    SERIES_SOLO,
    LINKS_OUT,
    ESCAPING_POST,
    LIQUID_LINKS_OUT,
    LINKED,
    LIQUID_LINKED,
    LINKS_OUT_TWO,
    ALPHA_THREE,
    ALPHA_BETA,
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
