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

<div class="card-grid card-grid-1">
  {% assign sorted_posts = site.posts | sort: 'date' | reverse %}
  {% for post in sorted_posts limit:5 %}
  <a href="{{ post.url }}" class="card-link">
    <article class="card">
      <div class="card-content">
        <h4 class="card-title">{{ post.title }}</h4>
        <span class="card-meta">{{ post.date | date_to_long_string }}</span>
        <div class="card-body">
          {% if post.summary %}
            {% for paragraph in post.summary limit:1 %}
              <p>{{ paragraph.p }}</p>
            {% endfor %}
          {% else %}
            {{ post.excerpt }}
          {% endif %}
        </div>
      </div>
    </article>
  </a>
  {% endfor %}
</div>

<p class="view-all-link"><a href="/essays/all/">View all essays &rarr;</a></p>
