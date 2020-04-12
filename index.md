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

<div class="row">
  <article class="col-4 col-12-xsmall work-item">
    <a href="images/fulls/01.jpg" class="image fit thumb"><img src="images/thumbs/01.jpg" alt="" /></a>
    <h3>Magna sed consequat tempus</h3>
    <p>Lorem ipsum dolor sit amet nisl sed nullam feugiat.</p>
  </article>
  <article class="col-4 col-12-xsmall work-item">
    <a href="images/fulls/02.jpg" class="image fit thumb"><img src="images/thumbs/02.jpg" alt="" /></a>
    <h3>Ultricies lacinia interdum</h3>
    <p>Lorem ipsum dolor sit amet nisl sed nullam feugiat.</p>
  </article>
  <article class="col-4 col-12-xsmall work-item">
    <a href="images/fulls/03.jpg" class="image fit thumb"><img src="images/thumbs/03.jpg" alt="" /></a>
    <h3>Tortor metus commodo</h3>
    <p>Lorem ipsum dolor sit amet nisl sed nullam feugiat.</p>
  </article>
</div>

<ul class="actions">
  <li><a href="#" class="button small">About Me</a></li>
  <li><a href="#" class="button small">Portfolio</a></li>
</ul>

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