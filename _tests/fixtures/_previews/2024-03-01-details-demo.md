---
title: Collapsible box demo
date: 2024-03-01
---

A fixture preview for test_details.py, injected into the designed build only (see
_tests/corpus.py). It uses the collapsible box includes the way an essay would:
one box closed by default, holding a heading, a list, a footnote and a reference
link defined outside the box, and one box that starts open. Like every preview it
is unlisted and carries `noindex`.

Before the boxes: a footnote[^outer] and a [reference link][ref].

{% include details_open.html summary="A **closed** box" %}

### Inside the box

Detail with *emphasis*, a footnote[^inner] and the same [reference link][ref].

- first item
- second item

{% include details_close.html %}

{% include details_open.html summary='An "open" box' open=true %}

This box starts open.

{% include details_close.html %}

After the boxes.

[ref]: https://example.com/
[^outer]: The footnote outside the box.
[^inner]: The footnote inside the box.
