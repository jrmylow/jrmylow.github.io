---
layout: default
# Basic title information
title: Jeremy Low
subtitle: 
summary: 
- p: A simple page to call my own

# Sections if needed
sections:

---

## About
Placeholder for introductory section and portfolio. Soon to be updated


---

## Recent Posts
<ul>
  {% assign sorted_posts = (site.posts | sort: 'date') | reverse %}

  {% for post in sorted_posts limit: 5 %}
    <h3><a href="{{ post.url }}">{{ post.title }}</a></h3>
      {% for paragraph in post.summary %}
        <p>{{ paragraph.p }}</p>
      {% endfor %}
  {% endfor %}
</ul>
<a href="#" class="button small">All Posts</a>