---
layout: page
title: Essays
permalink: /essays/
---
> "Writing is nature's way of telling us how lousy our thinking is."
>
> Leslie Lamport

I am writing to sharpen my thinking and indulge my curiosity. All mistakes and inaccuracies in these are my own. If you find one, I'd appreciate you [reaching out](/contact) and letting me know.

<!-- TODO: Add a section for curated / top posts -->

<!-- TODO: Add a section for posts by topic - collapsible -->

### Recent Essays
<p>
  {% assign sorted_posts = site.posts | sort: 'date' | reverse %}

  {% for post in sorted_posts %}
    {{post.date | date_to_long_string}} - <b><a href="{{ post.url }}">{{ post.title }}</a></b><p>
  {% endfor %}
</p>
