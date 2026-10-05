"""corpus.py: the designed build's content spec and its scale filler."""

import datetime as dt

import corpus
import pytest
import yaml


def test_scale_fills_to_the_requested_total():
    posts = corpus.posts(250)
    assert len(posts) == 250
    assert len({post.filename for post in posts}) == 250, "file names must be unique"


def test_filler_is_older_than_every_designed_case():
    """Newest-first pages (home, /essays/) keep showing the designed cases at any scale."""
    oldest_designed = min(post.date for post in corpus.DESIGNED)
    assert all(post.date < oldest_designed for post in corpus.posts(250)[len(corpus.DESIGNED) :])


def test_scale_below_the_designed_cases_is_refused():
    with pytest.raises(ValueError, match="scale-posts"):
        corpus.posts(len(corpus.DESIGNED) - 1)


def test_front_matter_survives_yaml_quoting():
    """Titles with markup-significant characters reach Jekyll intact."""
    title = 'Q&A: <tags> and "quotes"'
    post = corpus.Post(dt.date(2025, 1, 2), "q-and-a", title, ("a", "b"))
    front = yaml.safe_load(post.render().split("---\n")[1])
    assert front == {"layout": "post", "title": title, "date": dt.date(2025, 1, 2), "tags": ["a", "b"]}
