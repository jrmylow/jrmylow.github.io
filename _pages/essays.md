---
layout: page
title: Essays
permalink: /essays/
---
My best work:
<p>
{% assign top_posts = site.posts | where_exp: "item", "item.tags contains 'top'" | sort: 'date' | reverse %}
  {% for post in top_posts %}
    <b><a href="{{ post.url }}">{{ post.title }}</a></b>
      {% for paragraph in post.summary %}
        <p>{{ paragraph.p }}</p>
      {% endfor %}
  {% endfor %}
</p>

### Recent Essays
<p>
  {% assign sorted_posts = site.posts | sort: 'date' | reverse %}

  {% for post in sorted_posts %}
    {{post.date | date_to_long_string}} - <b><a href="{{ post.url }}">{{ post.title }}</a></b><p>
  {% endfor %}
</p>