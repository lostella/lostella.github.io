---
layout: default
title: "Blog"
description: "Blog posts."
keywords: "blog, post, posts"
permalink: /blog/
---

# Blog posts

<ul>
  {% for post in site.posts %}
    <li>
      {{ post.date | date: "%A, %B %d, %Y" }} &mdash; <a href="{{ post.url }}">{{ post.title }}</a>
    </li>
  {% endfor %}
</ul>
