# lostella.github.io

https://lostella.github.io

## Usage

```sh
uv run pytest  # run tests
uv run build   # render content/ into public/
uv run serve   # serve public/ at http://127.0.0.1:8000/
```

## Layout

```
content/       pages and posts; *.md is rendered, anything else is copied alongside it
  index.md       the home page
  <name>.md      a page at /<name>/, listed in the nav if it has menu = "main"
  blog/<name>.md a post at /blog/<name>/
static/        copied verbatim to the site root
style.css      the stylesheet
website.py     the generator
```

Pages carry TOML front matter between `+++` fences:

```toml
+++
title = "A post about something"
date = "2020-01-31"
updated = "2020-02-14"
description = "One or two sentences, used for the meta tags."
tags = ["a tag", "another tag"]
aliases = ["/blog/2020/01/31/an-older-url"]
+++
```

`$inline$` and `$$display$$` math is converted to MathML at build time.

The build writes the pages, the blog index, per-tag pages, alias redirects,
`404.html`, `sitemap.xml` and `robots.txt`.
