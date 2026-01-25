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
  Tag Cloud
{% endcomment %}
<div class="tag-cloud">
{% for tag in unique_tags %}
  {% assign count = all_tags | where_exp: "t", "t == tag" | size %}
  {% comment %} Calculate weight 1-5 based on count {% endcomment %}
  {% assign weight_raw = count | times: 4 | divided_by: max_count | plus: 1 %}
  {% if weight_raw > 5 %}{% assign weight = 5 %}{% else %}{% assign weight = weight_raw %}{% endif %}
  <a href="#{{ tag }}" class="tag-cloud-item" data-weight="{{ weight }}">{{ tag }} ({{ count }})</a>
{% endfor %}
</div>

{% comment %}
  Tag Sections - each tag with its posts
{% endcomment %}
{% for tag in unique_tags %}
{% assign tagged_posts = site.posts | where_exp: "post", "post.tags contains tag" %}
<div class="tag-section" id="{{ tag }}">
  <h3 class="tag-section-title">{{ tag }} <span class="tag-count">({{ tagged_posts.size }})</span></h3>
  <ul class="tag-post-list">
  {% for post in tagged_posts %}
    <li class="tag-post-item">
      <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
      <span class="tag-post-date">{{ post.date | date: "%B %d, %Y" }}</span>
    </li>
  {% endfor %}
  </ul>
</div>
{% endfor %}
