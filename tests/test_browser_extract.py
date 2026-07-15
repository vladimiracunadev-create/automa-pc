"""Tests de la familia de extracción web (casos 21–27).

Toda la lógica (links, hash, tracking, markdown, CSV, BFS, robots) se prueba
sin Playwright: el glue de navegador es mínimo y ``scrape_page`` acepta
cualquier objeto con la interfaz de una Page (acá, ``FakePage``).
"""
from __future__ import annotations

import json

from actions.browser_extract import (
    RobotsCache,
    apply_tracking,
    build_result,
    content_hash,
    crawl_pages,
    normalize_text,
    parse_number,
    render_markdown,
    resolve_links,
    save_tables_csv,
    scrape_page,
)
from actions.http_actions import check_urls

BASE = "https://example.com/docs/index.html"


# ---------------------------------------------------------------------------
# Normalización, hash y parseo numérico
# ---------------------------------------------------------------------------

def test_normalize_text_collapses_blank_lines():
    raw = "  hola  \n\n\n\n mundo \n\n"
    assert normalize_text(raw) == "hola\n\nmundo"


def test_content_hash_stable_and_sensitive():
    assert content_hash("abc") == content_hash("abc")
    assert content_hash("abc") != content_hash("abd")


def test_parse_number_formats():
    assert parse_number("$ 1.499,90") == 1499.9
    assert parse_number("1,499.90 USD") == 1499.9
    assert parse_number("42") == 42
    assert parse_number("1.499") == 1499  # separador de miles
    assert parse_number("0.5") == 0.5
    assert parse_number("-12,5 °C") == -12.5
    assert parse_number("sin numeros") is None
    assert parse_number(None) is None
    assert parse_number("") is None


# ---------------------------------------------------------------------------
# Resolución de links
# ---------------------------------------------------------------------------

def test_resolve_links_absolute_dedupe_and_order():
    anchors = [
        {"text": "A", "href": "page_a.html"},
        {"text": "A otra vez", "href": "page_a.html"},
        {"text": "Raíz", "href": "/index.html"},
        {"text": "Ancla", "href": "#seccion"},
        {"text": "JS", "href": "javascript:void(0)"},
        {"text": "Mail", "href": "mailto:x@y.z"},
        {"text": "Frag", "href": "page_a.html#frag"},
    ]
    links, truncated = resolve_links(anchors, BASE)
    assert [link["url"] for link in links] == [
        "https://example.com/docs/page_a.html",
        "https://example.com/index.html",
        "mailto:x@y.z",
    ]
    assert truncated is False


def test_resolve_links_respects_max_links():
    anchors = [{"text": str(i), "href": f"p{i}.html"} for i in range(5)]
    links, truncated = resolve_links(anchors, BASE, max_links=3)
    assert len(links) == 3
    assert truncated is True


# ---------------------------------------------------------------------------
# Tracking persistente
# ---------------------------------------------------------------------------

def test_apply_tracking_baseline_then_change(tmp_path):
    state = tmp_path / "watch.json"
    first = apply_tracking(str(state), "u", "hash1")
    assert first["first_run"] is True and first["changed"] is False

    same = apply_tracking(str(state), "u", "hash1")
    assert same["first_run"] is False and same["changed"] is False

    changed = apply_tracking(str(state), "u", "hash2")
    assert changed["changed"] is True
    assert changed["previous_value"] == "hash1"


def test_apply_tracking_recovers_from_corrupt_state(tmp_path):
    state = tmp_path / "watch.json"
    state.write_text("{corrupto", encoding="utf-8")
    out = apply_tracking(str(state), "u", "hash1")
    assert out["first_run"] is True
    assert json.loads(state.read_text(encoding="utf-8"))["watch_value"] == "hash1"


# ---------------------------------------------------------------------------
# Markdown y CSV
# ---------------------------------------------------------------------------

def test_render_markdown_includes_sections():
    md = render_markdown(
        {
            "title": "Título",
            "url": "https://x",
            "content_hash": "abc",
            "meta": {"description": "desc"},
            "text": "cuerpo",
            "tables": [[["c1", "c2"], ["v1", "v2"]]],
            "links": [{"text": "L", "url": "https://x/l"}],
        }
    )
    assert md.startswith("# Título")
    assert "| c1 | c2 |" in md
    assert "- [L](https://x/l)" in md
    assert "cuerpo" in md


def test_save_tables_csv_writes_one_file_per_table(tmp_path):
    paths = save_tables_csv([[["a", "b"], ["1", "2"]], [["x"]]], str(tmp_path / "out"))
    assert len(paths) == 2
    assert (tmp_path / "out" / "table_01.csv").read_text(encoding="utf-8").startswith("a,b")


# ---------------------------------------------------------------------------
# build_result + scrape_page con FakePage (sin Playwright)
# ---------------------------------------------------------------------------

class FakeElement:
    def __init__(self, text):
        self._text = text

    def inner_text(self):
        return self._text


class FakePage:
    """Duck-type mínimo de playwright Page para scrape_page."""

    def __init__(self, title="Demo", body="Precio: $ 1.499,90", anchors=None, meta=None, tables=None, selectors=None):
        self._title = title
        self._body = body
        self._anchors = anchors or [{"text": "A", "href": "a.html"}]
        self._meta = meta or [{"key": "description", "value": "una demo"}]
        self._tables = tables or [[["h1", "h2"], ["v1", "v2"]]]
        self._selectors = selectors or {}

    def title(self):
        return self._title

    def inner_text(self, _selector):
        return self._body

    def eval_on_selector_all(self, selector, _js):
        if selector == "a[href]":
            return self._anchors
        if selector.startswith("meta"):
            return self._meta
        if selector == "table":
            return self._tables
        raise AssertionError(f"selector inesperado: {selector}")

    def query_selector(self, selector):
        if selector in self._selectors:
            return FakeElement(self._selectors[selector])
        return None


def test_scrape_and_build_result_full(tmp_path):
    page = FakePage(selectors={"#precio": " $ 1.499,90 "})
    raw = scrape_page(page, selector="#precio", include_tables=True)
    result = build_result(
        raw,
        "https://example.com/x",
        selector="#precio",
        parse_number_flag=True,
        include_tables=True,
        track_state_path=str(tmp_path / "state.json"),
        save_markdown_path=str(tmp_path / "page.md"),
        save_tables_dir=str(tmp_path / "tables"),
    )
    assert result["title"] == "Demo"
    assert result["selector_found"] is True
    assert result["selector_number"] == 1499.9
    assert result["links_count"] == 1
    assert result["meta"]["description"] == "una demo"
    assert result["tables_count"] == 1
    assert result["first_run"] is True
    assert (tmp_path / "page.md").exists()
    assert (tmp_path / "tables" / "table_01.csv").exists()
    # todo el resultado debe ser JSON-serializable (va al histórico SQLite)
    json.dumps(result)


def test_build_result_selector_missing_reports_not_found():
    raw = scrape_page(FakePage(), selector="#no_existe")
    result = build_result(raw, "https://example.com/x", selector="#no_existe")
    assert result["selector_found"] is False
    assert result["selector_value"] is None


def test_build_result_truncates_text():
    raw = {"title": "t", "body_text": "x" * 100, "anchors": [], "meta": {}}
    result = build_result(raw, "https://x", max_text_chars=10)
    assert result["text_chars"] == 10
    assert result["text_truncated"] is True


# ---------------------------------------------------------------------------
# Crawl BFS (fetcher fake, sin navegador)
# ---------------------------------------------------------------------------

SITE = {
    "https://s.com/": {"title": "root", "body_text": "raiz", "anchors": [
        {"text": "a", "href": "/a"}, {"text": "b", "href": "/b"}, {"text": "ext", "href": "https://otro.com/x"},
    ]},
    "https://s.com/a": {"title": "a", "body_text": "pagina a", "anchors": [{"text": "c", "href": "/c"}]},
    "https://s.com/b": {"title": "b", "body_text": "pagina b", "anchors": [{"text": "a", "href": "/a"}]},
    "https://s.com/c": {"title": "c", "body_text": "pagina c", "anchors": []},
}


def _fetch(url):
    if url not in SITE:
        raise RuntimeError(f"404: {url}")
    return SITE[url]


def test_crawl_pages_bfs_order_and_depth():
    report = crawl_pages(_fetch, "https://s.com/", max_pages=10, max_depth=2)
    urls = [(p["url"], p["depth"]) for p in report["pages"]]
    assert urls == [
        ("https://s.com/", 0),
        ("https://s.com/a", 1),
        ("https://s.com/b", 1),
        ("https://s.com/c", 2),
    ]
    assert report["truncated"] is False
    assert report["errors"] == []


def test_crawl_pages_same_domain_filter():
    report = crawl_pages(_fetch, "https://s.com/", max_pages=10, max_depth=3)
    assert all(p["url"].startswith("https://s.com/") for p in report["pages"])


def test_crawl_pages_max_pages_marks_truncated():
    report = crawl_pages(_fetch, "https://s.com/", max_pages=2, max_depth=3)
    assert report["pages_count"] == 2
    assert report["truncated"] is True


def test_crawl_pages_max_depth_zero_only_start():
    report = crawl_pages(_fetch, "https://s.com/", max_pages=10, max_depth=0)
    assert report["pages_count"] == 1


def test_crawl_pages_error_does_not_abort():
    def flaky(url):
        if url == "https://s.com/a":
            raise RuntimeError("boom")
        return _fetch(url)

    report = crawl_pages(flaky, "https://s.com/", max_pages=10, max_depth=2)
    assert [e["url"] for e in report["errors"]] == ["https://s.com/a"]
    assert {p["url"] for p in report["pages"]} == {"https://s.com/", "https://s.com/b"}


def test_crawl_pages_robots_check_blocks():
    report = crawl_pages(
        _fetch,
        "https://s.com/",
        max_pages=10,
        max_depth=2,
        robots_check=lambda url: not url.endswith("/b"),
    )
    assert report["robots_blocked"] == ["https://s.com/b"]
    assert all(p["url"] != "https://s.com/b" for p in report["pages"])


# ---------------------------------------------------------------------------
# RobotsCache
# ---------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text


def test_robots_cache_disallow(monkeypatch):
    import requests

    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _FakeResponse(200, "User-agent: *\nDisallow: /privado/")
    )
    cache = RobotsCache()
    assert cache.allows("https://x.com/publico.html") is True
    assert cache.allows("https://x.com/privado/doc.html") is False


def test_robots_cache_missing_robots_allows(monkeypatch):
    import requests

    monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(404))
    cache = RobotsCache()
    assert cache.allows("https://x.com/lo-que-sea") is True


def test_robots_cache_non_http_always_allowed():
    cache = RobotsCache()
    assert cache.allows("file:///C:/local/pagina.html") is True


# ---------------------------------------------------------------------------
# http.check_urls
# ---------------------------------------------------------------------------

def test_check_urls_file_scheme(tmp_path):
    existing = tmp_path / "ok.html"
    existing.write_text("x", encoding="utf-8")
    missing = tmp_path / "no.html"
    out = check_urls([existing.as_uri(), missing.as_uri(), "mailto:a@b.c"])
    assert out["checked_count"] == 2
    assert out["ok_count"] == 1
    assert out["broken_count"] == 1
    assert out["broken"] == [missing.as_uri()]
    assert out["skipped_count"] == 1


def test_check_urls_empty_list():
    out = check_urls([])
    assert out["total_input"] == 0
    assert out["broken_count"] == 0


def test_check_urls_max_urls_truncates(tmp_path):
    files = []
    for i in range(4):
        f = tmp_path / f"f{i}.html"
        f.write_text("x", encoding="utf-8")
        files.append(f.as_uri())
    out = check_urls(files, max_urls=2)
    assert out["truncated"] is True
    assert len(out["results"]) == 2
