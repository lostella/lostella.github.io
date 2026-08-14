# lostella.github.io

https://lostella.github.io

## Usage

```sh
uv run build   # render content/ into public/
uv run serve   # serve public/ at http://127.0.0.1:8000/
```

## Layout

```
content/       pages and posts; *.md is rendered, anything else is copied verbatim
  index.md       the home page
  <name>.md      a page at /<name>/, listed in the nav if it has menu = "main"
  blog/<name>.md a post at /blog/<name>/
style.css      the stylesheet
website.py     the generator
```

Pages carry TOML front matter between `+++` fences:

```toml
+++
title = "Iterative methods done right"
date = "2018-07-25"
updated = "2023-03-12"
description = "Notes on the implementation of iterative methods in Julia."
tags = ["iterative methods", "julia"]
aliases = ["/blog/2018/07/25/iterative-methods-done-right"]
+++
```

`$inline$` and `$$display$$` math is converted to MathML at build time.

The build writes the pages, the blog index, per-tag pages, alias redirects,
`404.html`, `sitemap.xml` and `robots.txt`.
