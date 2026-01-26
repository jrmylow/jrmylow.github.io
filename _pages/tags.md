---
layout: page
title: Tags
permalink: /tags/
---

{% comment %}
  Collect all tags and count posts per tag
{% endcomment %}
{% assign all_tags = "" | split: "" %}
{% for post in site.posts %}
  {% for tag in post.tags %}
    {% assign all_tags = all_tags | push: tag %}
  {% endfor %}
{% endfor %}

{% comment %}
  Get unique tags sorted alphabetically
{% endcomment %}
{% assign unique_tags = all_tags | uniq | sort_natural %}

{% comment %}
  Calculate max count for weight scaling
{% endcomment %}
{% assign max_count = 1 %}
{% for tag in unique_tags %}
  {% assign count = all_tags | where_exp: "t", "t == tag" | size %}
  {% if count > max_count %}
    {% assign max_count = count %}
  {% endif %}
{% endfor %}

{% comment %}
  Tag Cloud - clickable toggle buttons
{% endcomment %}
<p>To filter all posts on this site, select tags that you are interested in. The essays shown will match all tags you select.</p>

<div class="tag-cloud">
{% for tag in unique_tags %}
  {% assign count = all_tags | where_exp: "t", "t == tag" | size %}
  <button type="button" class="tag-cloud-item" data-tag="{{ tag }}">{{ tag }} ({{ count }})</button>
{% endfor %}
</div>

{% comment %}
  Posts Container - flat list, hidden by default
{% endcomment %}
<div class="tag-posts-container">
  <ul class="tag-post-list">
  {% for post in site.posts %}
    {% assign post_tags = post.tags | join: "," %}
    <li class="tag-post-item" data-tags="{{ post_tags }}">
      <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
      <span class="tag-post-date">{{ post.date | date: "%B %d, %Y" }}</span>
    </li>
  {% endfor %}
  </ul>
</div>
