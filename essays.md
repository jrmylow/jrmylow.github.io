---
layout: page
title: Essays
---
<ul>
  {% assign sorted_posts = site.posts | sort: 'date' | reverse %}

  {% for post in sorted_posts %}
    <h3><a href="{{ post.url }}">{{ post.title }}</a></h3>
      {% for paragraph in post.summary %}
        <p>{{ paragraph.p }}</p>
      {% endfor %}
  {% endfor %}
</ul>