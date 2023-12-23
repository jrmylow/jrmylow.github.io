---
layout: default
# Basic title information
title: Home page
subtitle: 
summary: 
- p: A simple page to call my own

# Sections if needed
sections:

---

### Welcome
My name is Jeremy, and you can find me here at [jrmylow.com]({{site.url}}). I help people solve problems in planning and coordination, and dealing with complex systems at scale.

I am deeply interested in all things tech and engineering (and plenty outside that). For more about me, see [here](/about).

<!-- My essays are [here](/essays). -->

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

