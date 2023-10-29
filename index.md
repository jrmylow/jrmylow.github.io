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

### About
Placeholder for introductory section and portfolio. Soon to be updated

"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

---

### Recent Posts
<!-- The essays I have enjoyed the most are [here](). If you are looking for all posts instead, follow [this](). -->

{% assign sorted_posts = site.posts | sort: 'date' | reverse %}

{% for post in sorted_posts limit: 5 %}
<h6><a href="{{ post.url }}">{{ post.title }}</a></h6>
{% for paragraph in post.summary %}
<p>{{ paragraph.p }}</p>
{% endfor %}
{% endfor %}

<a href="#">All Posts</a>

