---
layout: page
title: Blog
weight: 4
is_blog_home: true
description: "Lorenzo Stella's blog."
permalink: /blog/
---

Blog posts (most recent first):

<ul>
  {% for post in site.posts %}
    <li>
      {{ post.date | date: "%A %B %d, %Y" }} &mdash; <a href="{{ post.url }}">{{ post.title }}</a>
    </li>
  {% endfor %}
</ul>
