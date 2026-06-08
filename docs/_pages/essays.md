---
layout: page
title: Essays
permalink: /essays/
nav_order: 30
---
> "Writing is nature's way of telling us how lousy our thinking is."
>
> Leslie Lamport

I am writing to sharpen my thinking and indulge my curiosity. All mistakes and inaccuracies in these are my own. If you find one, I'd appreciate you [reaching out](/contact) and letting me know.

<!-- TODO: Add a section for curated / top posts -->

<!-- TODO: Add a section for posts by topic - collapsible -->

### Recent Essays

<div class="card-grid card-grid-1">
  {% assign sorted_posts = site.posts | sort: 'date' | reverse %}
  {% for post in sorted_posts limit:5 %}
  {% include post_card.html post=post heading="h4" %}
  {% endfor %}
</div>

<p class="view-all-link"><a href="/essays/all/">View all essays &rarr;</a></p>
