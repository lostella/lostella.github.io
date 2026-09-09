"""Tests for the site generator. Run with ``uv run pytest``."""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ElementTree
from datetime import date
from pathlib import Path

import pytest

import website
from website import (
    Page,
    build,
    escape,
    load_page,
    navigation,
    parse_front_matter,
    render_markdown,
    summarize,
    tag_slug,
    typographize,
)

# --------------------------------------------------------------------------
# Typography
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("life's", "life’s"),
        ('He said "hello".', "He said “hello”."),
        ('("quoted")', "(“quoted”)"),
        ("a -- b", "a – b"),
        ("a --- b", "a — b"),
        ("wait...", "wait…"),
    ],
)
def test_typographize(source: str, expected: str) -> None:
    assert typographize(source) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/some--path?a=1",
        "http://example.com/a--b--c",
        "www.example.com/x--y",
    ],
)
def test_typographize_leaves_urls_alone(url: str) -> None:
    assert typographize(f"See {url} for more.") == f"See {url} for more."


def test_typographize_still_curls_around_a_url() -> None:
    result = typographize("It's at https://example.com/a--b -- go read it")
    assert result == "It’s at https://example.com/a--b – go read it"


def test_code_spans_are_not_typographized() -> None:
    body = render_markdown("Use `--verbose` and it's fine.")
    assert "<code>--verbose</code>" in body
    assert "it’s" in body


# --------------------------------------------------------------------------
# Summaries
# --------------------------------------------------------------------------


def test_summarize_unescapes_entities() -> None:
    body = render_markdown("Tom & Jerry are 5 < 6.")
    summary = summarize(body)
    assert summary == "Tom & Jerry are 5 < 6."
    # The one escape at render time must be the only one applied.
    assert escape(summary) == "Tom &amp; Jerry are 5 &lt; 6."


def test_summarize_drops_math() -> None:
    body = render_markdown("Consider $$x^2 + y^2 = z^2$$ and more text here.")
    assert "<math" in body
    assert summarize(body) == "Consider and more text here."


def test_summarize_drops_code_blocks() -> None:
    body = render_markdown("Intro line.\n\n```python\nimport os\n```\n")
    assert summarize(body) == "Intro line."


def test_summarize_marks_truncation() -> None:
    long = render_markdown(" ".join(["word"] * (website.SUMMARY_WORDS + 10)))
    summary = summarize(long)
    assert summary.endswith("…")
    assert len(summary.split()) == website.SUMMARY_WORDS


def test_summarize_does_not_mark_short_text() -> None:
    assert summarize(render_markdown("Just a few words.")) == "Just a few words."


# --------------------------------------------------------------------------
# Front matter
# --------------------------------------------------------------------------


def test_parse_front_matter_without_fence() -> None:
    assert parse_front_matter("no front matter\n") == ({}, "no front matter\n")


def test_parse_front_matter_reads_toml() -> None:
    meta, body = parse_front_matter('+++\ntitle = "x"\n+++\n\nbody\n')
    assert meta == {"title": "x"}
    assert body == "body\n"


def test_parse_front_matter_keeps_fences_in_the_body() -> None:
    _, body = parse_front_matter('+++\ntitle = "x"\n+++\n\nbefore\n\n+++\n\nafter\n')
    assert "+++" in body


def test_parse_front_matter_rejects_unterminated_fence() -> None:
    with pytest.raises(ValueError, match="unterminated"):
        parse_front_matter('+++\ntitle = "x"\n\nno closing fence\n')


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------


@pytest.fixture
def content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty content root that ``load_page`` and ``build`` will read from."""
    root = tmp_path / "content"
    root.mkdir()
    monkeypatch.setattr(website, "CONTENT", root)
    return root


def write_page(content: Path, relative: str, text: str) -> Path:
    path = content / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("relative", "url", "is_post"),
    [
        ("index.md", "/", False),
        ("projects.md", "/projects/", False),
        ("blog/hello.md", "/blog/hello/", True),
        ("blog.md", "/blog/", False),
        ("blog/index.md", "/blog/", False),
    ],
)
def test_load_page_urls(content: Path, relative: str, url: str, is_post: bool) -> None:
    path = write_page(content, relative, '+++\ntitle = "T"\n+++\n\nbody\n')
    page = load_page(path)
    assert page.url == url
    assert page.is_post is is_post


def test_load_page_typographizes_title_and_description(content: Path) -> None:
    path = write_page(
        content,
        "blog/hello.md",
        '+++\ntitle = "life\'s work"\ndescription = "it\'s here"\n+++\n\nbody\n',
    )
    page = load_page(path)
    assert page.title == "life’s work"
    assert page.description == "it’s here"


def test_load_page_falls_back_to_a_summary(content: Path) -> None:
    path = write_page(content, "a.md", "+++\n+++\n\nSome body prose.\n")
    assert load_page(path).description == "Some body prose."


def test_load_page_names_the_file_in_errors(content: Path) -> None:
    path = write_page(content, "broken.md", '+++\ntitle = "x"\n\nno close\n')
    with pytest.raises(ValueError, match="broken.md") as caught:
        load_page(path)
    assert "unterminated" in str(caught.value)


# --------------------------------------------------------------------------
# Templates
# --------------------------------------------------------------------------


def test_navigation_escapes_titles() -> None:
    page = Page(
        url="/r-and-d/",
        title="R & D",
        body="",
        description="",
        date=None,
        updated=None,
        tags=(),
        aliases=(),
        in_menu=True,
        is_post=False,
    )
    assert "R &amp; D" in navigation([page], "/")


def test_navigation_marks_the_current_page() -> None:
    assert 'href="/blog/" aria-current="page"' in navigation([], "/blog/some-post/")


@pytest.mark.parametrize(
    ("tag", "slug"),
    [("julia", "julia"), ("iterative methods", "iterative-methods")],
)
def test_tag_slug(tag: str, slug: str) -> None:
    assert tag_slug(tag) == slug


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------


@pytest.fixture
def output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "public"
    monkeypatch.setattr(website, "OUTPUT", target)
    return target


def test_build_rejects_colliding_tag_slugs(content: Path, output: Path) -> None:
    write_page(content, "index.md", "+++\n+++\n\nhome\n")
    for name, tag in (("a", "C++"), ("b", "C#")):
        write_page(
            content,
            f"blog/{name}.md",
            f'+++\ntitle = "{name}"\ndate = "2020-01-01"\ntags = ["{tag}"]\n+++\n\nx\n',
        )
    with pytest.raises(ValueError, match="share the slug"):
        build()


def test_build_rejects_tags_without_a_slug(content: Path, output: Path) -> None:
    write_page(content, "index.md", "+++\n+++\n\nhome\n")
    write_page(
        content,
        "blog/a.md",
        '+++\ntitle = "a"\ndate = "2020-01-01"\ntags = ["###"]\n+++\n\nx\n',
    )
    with pytest.raises(ValueError, match="no usable slug"):
        build()


def test_build_logs_what_it_wrote(
    content: Path, output: Path, caplog: pytest.LogCaptureFixture
) -> None:
    write_page(content, "index.md", "+++\n+++\n\nhome\n")
    with caplog.at_level(logging.INFO, logger="website"):
        build()
    messages = [record.getMessage() for record in caplog.records]
    assert any("built 3 pages" in message for message in messages)
    assert any(
        record.levelno == logging.WARNING and "no posts" in record.getMessage()
        for record in caplog.records
    )


# The real site, built into a temporary directory.


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    target = tmp_path_factory.mktemp("site") / "public"
    original = website.OUTPUT
    website.OUTPUT = target
    try:
        build()
    finally:
        website.OUTPUT = original
    return target


def test_site_has_the_expected_files(site: Path) -> None:
    for relative in (
        "index.html",
        "blog/index.html",
        "blog/iterative-methods-done-right/index.html",
        "blog/2018/07/25/iterative-methods-done-right/index.html",
        "tags/julia/index.html",
        "404.html",
        "sitemap.xml",
        "robots.txt",
        "style.css",
        "keybase.txt",
    ):
        assert (site / relative).is_file(), relative


def test_site_is_never_double_escaped(site: Path) -> None:
    for path in site.rglob("*.html"):
        assert "amp;amp;" not in path.read_text(encoding="utf-8"), path


def test_site_typographizes_titles(site: Path) -> None:
    post = site / "blog/iterative-methods-done-right/index.html"
    assert "life’s" in post.read_text(encoding="utf-8")


def test_site_descriptions_are_plain_prose(site: Path) -> None:
    for path in site.rglob("*.html"):
        for description in re.findall(
            r'<meta name="description" content="([^"]*)"', path.read_text("utf-8")
        ):
            assert "&#x" not in description, path  # MathML character references
            assert "&amp;" not in description, path


HREF_RE = re.compile(r'href="(/[^"#?]*)')


def test_site_internal_links_resolve(site: Path) -> None:
    broken: list[str] = []
    for path in sorted(site.rglob("*.html")):
        for href in HREF_RE.findall(path.read_text(encoding="utf-8")):
            target = site / href.strip("/")
            if not (target.is_file() or (target / "index.html").is_file()):
                broken.append(f"{path.relative_to(site)} -> {href}")
    assert not broken


def test_site_sitemap_is_well_formed(site: Path) -> None:
    root = ElementTree.parse(site / "sitemap.xml").getroot()
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    locations = [element.text for element in root.iter(f"{namespace}loc")]
    assert f"{website.BASE_URL}/" in locations
    assert f"{website.BASE_URL}/blog/" in locations
    for element in root.iter(f"{namespace}lastmod"):
        assert element.text is not None
        date.fromisoformat(element.text)
