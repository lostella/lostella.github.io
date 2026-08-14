"""Static site generator for lostella.github.io.

Reads Markdown with TOML front matter from ``content/``, renders it into
``public/``. ``build`` and ``serve`` are exposed as console scripts, so the
whole workflow is ``uv run build`` and ``uv run serve``.
"""

from __future__ import annotations

import functools
import re
import shutil
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from string import Template
from typing import Any

import mistune
from latex2mathml.converter import convert as latex_to_mathml

SITE_TITLE = "Lorenzo Stella"
BASE_URL = "https://lostella.github.io"
LANG = "en-us"
LOCALE = "en_us"
DATE_FORMAT = "%d %b, %Y"
SUMMARY_WORDS = 70
SERVE_PORT = 8000

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
STYLESHEET = ROOT / "style.css"
OUTPUT = ROOT / "public"


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------


def typographize(text: str) -> str:
    """Curl quotes and turn dash/ellipsis runs into their typographic form.

    Applied to text nodes only, so code spans, code blocks and math are left
    alone. This mirrors what Hugo's typographer did to the same content.
    """
    text = text.replace("---", "—").replace("--", "–").replace("...", "…")
    # Single quotes are apostrophes throughout this site's prose ("life's",
    # "hold 'em"), never quotation marks, so they always curl closing.
    text = text.replace("'", "’")
    out: list[str] = []
    for index, char in enumerate(text):
        if char != '"':
            out.append(char)
            continue
        previous = text[index - 1] if index else " "
        out.append("”" if previous.isalnum() or previous in ")]}’" else "“")
    return "".join(out)


class Renderer(mistune.HTMLRenderer):
    """HTML renderer that turns LaTeX into MathML at build time."""

    def text(self, text: str) -> str:
        return super().text(typographize(text))

    def block_math(self, text: str) -> str:
        return latex_to_mathml(text, display="block") + "\n"

    def inline_math(self, text: str) -> str:
        return latex_to_mathml(text, display="inline")


markdown = mistune.create_markdown(renderer=Renderer(escape=False), plugins=["math"])


def render_markdown(text: str) -> str:
    result = markdown(text)
    assert isinstance(result, str)
    return result


# --------------------------------------------------------------------------
# Content
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Page:
    url: str
    title: str
    body: str
    description: str
    date: date | None
    updated: date | None
    tags: tuple[str, ...]
    aliases: tuple[str, ...]
    in_menu: bool
    is_post: bool


TAG_RE = re.compile(r"<[^>]+>")
SLUG_RE = re.compile(r"[^a-z0-9]+")


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Split a ``+++``-fenced TOML header from the Markdown body."""
    if not text.startswith("+++"):
        return {}, text
    _, header, body = text.split("+++", 2)
    return tomllib.loads(header), body.lstrip("\n")


def as_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    return None


def summarize(body: str) -> str:
    """First ``SUMMARY_WORDS`` words of the rendered body, as plain text."""
    return " ".join(TAG_RE.sub(" ", body).split()[:SUMMARY_WORDS])


def load_page(path: Path) -> Page:
    meta, text = parse_front_matter(path.read_text(encoding="utf-8"))
    relative = path.relative_to(CONTENT).with_suffix("")
    url = "/" if relative.name == "index" else f"/{relative.as_posix()}/"
    body = render_markdown(text)
    return Page(
        url=url,
        title=meta.get("title", ""),
        body=body,
        description=meta.get("description") or summarize(body),
        date=as_date(meta.get("date")),
        updated=as_date(meta.get("updated")),
        tags=tuple(meta.get("tags", ())),
        aliases=tuple(meta.get("aliases", ())),
        in_menu=meta.get("menu") == "main",
        is_post=relative.parts[0] == "blog",
    )


def load_content() -> tuple[list[Page], list[Path]]:
    """Return the Markdown pages, and the asset files to copy verbatim."""
    pages: list[Page] = []
    assets: list[Path] = []
    for path in sorted(CONTENT.rglob("*")):
        if path.is_dir():
            continue
        if path.suffix == ".md":
            pages.append(load_page(path))
        else:
            assets.append(path)
    return pages, assets


def tag_slug(tag: str) -> str:
    return SLUG_RE.sub("-", tag.lower()).strip("-")


def tag_title(tag: str) -> str:
    return tag.title()


def tag_url(tag: str) -> str:
    return f"/tags/{tag_slug(tag)}/"


# --------------------------------------------------------------------------
# Templates
# --------------------------------------------------------------------------

BASE = Template("""<!DOCTYPE html>
<html lang="$lang">

<head>
  <meta http-equiv="X-Clacks-Overhead" content="GNU Terry Pratchett" />
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="referrer" content="no-referrer-when-downgrade" />
  <title>$title</title>
$meta
  <link rel="stylesheet" href="/style.css">
</head>

<body>
  <header>
    <a href="/" class="title">
      <h2>$site_title</h2>
    </a>
    <nav>$nav</nav>
  </header>
  <content>
$body
  </content>
</body>

</html>
""")

POST = Template("""<h1>$title</h1>
<p class="pubdate">
  <time datetime="$datetime" pubdate>$date</time>
</p>
$body
<p>
$tags
</p>
""")

LISTING = Template("""$heading<ul class="blog-posts">
$items
</ul>
$footer""")

FILTER_HEADING = Template("""<h3 style="margin-bottom:0">Filtering for "$title"</h3>
<small>
  <a href="/blog/">Remove filter</a>
</small>
""")

ALIAS = Template("""<!DOCTYPE html>
<html lang="$lang">
  <head>
    <title>$url</title>
    <link rel="canonical" href="$url">
    <meta name="robots" content="noindex">
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0; url=$url">
  </head>
</html>
""")

SITEMAP = Template("""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
$entries
</urlset>
""")

ROBOTS = f"User-agent: *\nSitemap: {BASE_URL}/sitemap.xml\n"

NOT_FOUND_BODY = "<h1>Page not found</h1>"


def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def meta_tags(
    *,
    title: str,
    url: str,
    description: str,
    keywords: tuple[str, ...],
    page: Page | None = None,
) -> str:
    """The SEO / OpenGraph / Twitter / schema.org block, as Hugo emitted it."""
    name = title or SITE_TITLE
    lines = [
        f'<meta name="title" content="{escape(name)}" />',
        f'<meta name="description" content="{escape(description)}" />',
        f'<meta name="keywords" content="{escape(",".join(keywords))}" />',
        f'<meta property="og:url" content="{BASE_URL}{url}">',
        f'<meta property="og:site_name" content="{SITE_TITLE}">',
        f'<meta property="og:title" content="{escape(name)}">',
        f'<meta property="og:description" content="{escape(description)}">',
        f'<meta property="og:locale" content="{LOCALE}">',
        f'<meta property="og:type" content="{"article" if page else "website"}">',
    ]
    if page is not None and page.is_post:
        assert page.date is not None, f"post {page.url} has no date"
        published = page.date.isoformat()
        modified = (page.updated or page.date).isoformat()
        lines += [
            '<meta property="article:section" content="blog">',
            f'<meta property="article:published_time" content="{published}">',
            f'<meta property="article:modified_time" content="{modified}">',
        ]
        lines += [
            f'<meta property="article:tag" content="{escape(tag_title(tag))}">'
            for tag in page.tags
        ]
    lines += [
        '<meta name="twitter:card" content="summary">',
        f'<meta name="twitter:title" content="{escape(name)}">',
        f'<meta name="twitter:description" content="{escape(description)}">',
        f'<meta itemprop="name" content="{escape(name)}">',
        f'<meta itemprop="description" content="{escape(description)}">',
    ]
    if page is not None and page.date is not None:
        modified = (page.updated or page.date).isoformat()
        lines += [
            f'<meta itemprop="datePublished" content="{page.date.isoformat()}">',
            f'<meta itemprop="dateModified" content="{modified}">',
        ]
    return "\n".join("  " + line for line in lines)


def navigation(menu: list[Page]) -> str:
    links = [("/", "Home")]
    links += [(page.url, page.title) for page in menu]
    links += [("/blog/", "Blog")]
    return "".join(
        f'<a href="{url}">{label}</a>\n    ' for url, label in links
    ).rstrip()


def render(
    *,
    title: str,
    url: str,
    body: str,
    description: str,
    keywords: tuple[str, ...],
    menu: list[Page],
    page: Page | None = None,
    document_title: str | None = None,
) -> str:
    if document_title is None:
        document_title = f"{title} | {SITE_TITLE}" if title else SITE_TITLE
    return BASE.substitute(
        lang=LANG,
        site_title=SITE_TITLE,
        title=escape(document_title),
        meta=meta_tags(
            title=title, url=url, description=description, keywords=keywords, page=page
        ),
        nav=navigation(menu),
        body=body.strip("\n"),
    )


def post_item(page: Page) -> str:
    assert page.date is not None
    return (
        "  <li>\n"
        f'    <time datetime="{page.date.isoformat()}" pubdate>'
        f"{page.date.strftime(DATE_FORMAT)}</time>\n"
        f'    <a href="{page.url}">{escape(page.title)}</a>\n'
        "  </li>"
    )


def tag_links(tags: tuple[str, ...], *, separator: str = "") -> str:
    return "\n".join(
        f'  <a href="{tag_url(tag)}">#{tag_title(tag)}</a>{separator}' for tag in tags
    )


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------


def write(url: str, html: str) -> None:
    if url.endswith("/"):
        path = OUTPUT / url.strip("/") / "index.html"
    else:
        path = OUTPUT / url.lstrip("/")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def sitemap_entries(urls: list[tuple[str, date | None]]) -> str:
    entries = []
    for url, lastmod in urls:
        entry = f"  <url>\n    <loc>{BASE_URL}{url}</loc>"
        if lastmod is not None:
            entry += f"\n    <lastmod>{lastmod.isoformat()}</lastmod>"
        entries.append(entry + "\n  </url>")
    return "\n".join(entries)


def build() -> None:
    """Render the whole site into ``public/``."""
    pages, assets = load_content()
    home = next(page for page in pages if page.url == "/")
    menu = sorted((page for page in pages if page.in_menu), key=lambda page: page.title)
    posts = sorted(
        (page for page in pages if page.is_post),
        key=lambda page: page.date or date.min,
        reverse=True,
    )

    tagged: dict[str, list[Page]] = defaultdict(list)
    for post in posts:
        for tag in post.tags:
            tagged[tag].append(post)
    all_tags = tuple(sorted(tagged, key=tag_slug))
    all_keywords = all_tags + ("",)

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    shutil.copyfile(STYLESHEET, OUTPUT / STYLESHEET.name)
    for asset in assets:
        target = OUTPUT / asset.relative_to(CONTENT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(asset, target)

    for page in pages:
        keywords = page.tags + ("",) if page.url != "/" else all_keywords
        if page.is_post:
            assert page.date is not None
            body = POST.substitute(
                title=escape(page.title),
                datetime=page.date.isoformat(),
                date=page.date.strftime(DATE_FORMAT),
                body=page.body.strip("\n"),
                tags=tag_links(page.tags),
            )
        else:
            body = page.body
        write(
            page.url,
            render(
                title=page.title,
                url=page.url,
                body=body,
                description=page.description,
                keywords=keywords,
                menu=menu,
                page=None if page.url == "/" else page,
            ),
        )
        for alias in page.aliases:
            url = f"{BASE_URL}{page.url}"
            write(alias.strip("/") + "/", ALIAS.substitute(lang=LANG, url=url))

    cloud = tag_links(all_tags, separator="&nbsp;")
    write(
        "/blog/",
        render(
            title="Blog",
            url="/blog/",
            body=LISTING.substitute(
                heading="",
                items="\n".join(post_item(post) for post in posts)
                or "  <li>No posts yet</li>",
                footer=f"<small>\n  <div>\n{cloud}\n  </div>\n</small>",
            ),
            description=f"Blog posts by {SITE_TITLE}.",
            keywords=all_keywords,
            menu=menu,
        ),
    )

    for tag, tag_posts in tagged.items():
        write(
            tag_url(tag),
            render(
                title=tag_title(tag),
                url=tag_url(tag),
                body=LISTING.substitute(
                    heading=FILTER_HEADING.substitute(title=tag_title(tag)),
                    items="\n".join(post_item(post) for post in tag_posts),
                    footer="",
                ),
                description=f"Blog posts tagged #{tag_title(tag)}.",
                keywords=(tag, ""),
                menu=menu,
            ),
        )

    write(
        "/404.html",
        render(
            title="404",
            url="/404.html",
            body=NOT_FOUND_BODY,
            description="Page not found.",
            keywords=all_keywords,
            menu=menu,
            document_title="404",
        ),
    )

    urls: list[tuple[str, date | None]] = [("/", home.updated or home.date)]
    urls += [(page.url, page.updated or page.date) for page in pages if page.url != "/"]
    urls += [("/blog/", posts[0].date if posts else None)]
    urls += [(tag_url(tag), tagged[tag][0].date) for tag in all_tags]
    (OUTPUT / "sitemap.xml").write_text(
        SITEMAP.substitute(entries=sitemap_entries(urls)), encoding="utf-8"
    )
    (OUTPUT / "robots.txt").write_text(ROBOTS, encoding="utf-8")

    count = len(list(OUTPUT.rglob("*.html")))
    print(f"built {count} pages into {OUTPUT.relative_to(ROOT)}/")


def serve() -> None:
    """Serve ``public/`` over HTTP. Builds nothing; run ``build`` first."""
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(OUTPUT))
    with ThreadingHTTPServer(("127.0.0.1", SERVE_PORT), handler) as httpd:
        print(f"serving http://127.0.0.1:{SERVE_PORT}/ — ctrl-c to stop")
        httpd.serve_forever()
