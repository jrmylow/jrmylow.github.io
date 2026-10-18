---
title: Collapsible box demo
date: 2024-03-01
---

A fixture preview for test_details.py, injected into the designed build only (see
_tests/corpus.py). It uses the collapsible box includes the way an essay would:
one box closed by default, holding a heading, a list, a footnote and a reference
link defined outside the box, one box that starts open, and one whose summary
wraps and holds a link. Like every preview it is unlisted and carries `noindex`.

Before the boxes: a footnote[^outer] and a [reference link][ref].

{% include details_open.html summary="A **closed** box" %}

## Inside the box

Detail with *emphasis*, a footnote[^inner] and the same [reference link][ref].

- first item
- second item

{% include details_close.html %}

{% include details_open.html summary='An "open" box' open=true %}

This box starts open.

{% include details_close.html %}

{% include details_open.html summary="A summary long enough to wrap onto more than one line at the default viewport width, as a project summary does, with a [link](https://example.com/) in it and a few more words after the link." %}

The link in the summary above stays in the flow of its sentence, outside the toggle.

{% include details_close.html %}

After the boxes.

[ref]: https://example.com/
[^outer]: The footnote outside the box.
[^inner]: The footnote inside the box.
