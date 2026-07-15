"""Extracción de contenido web con Playwright headless.

Mientras ``browser.capture_page`` fotografía el DOM renderizado (PNG), estas
acciones lo LEEN: título, texto visible, links, metadatos, tablas y valores
puntuales vía selector CSS. Sobre esa base se construyen los casos 21–27:
extractor de página, mapa de sitio, detector de cambios, auditor de links,
extractor de tablas, monitor de valor y archivado offline.

Diseño para testabilidad: la interacción con Playwright vive en
``scrape_page``/``extract_content``/``crawl_site`` (glue mínimo), y toda la
lógica (resolución de links, normalización, hash, tracking persistente,
markdown, CSV, BFS del crawl) son funciones puras testeables sin navegador.

Determinismo: el crawl es BFS con links en orden de aparición en el DOM,
sin aleatoriedad, acotado por ``max_pages``/``max_depth``. El contenido de una
web puede cambiar entre corridas — lo determinista es el comportamiento y la
estructura de salida, no el contenido remoto.

Repo upstream: https://github.com/microsoft/playwright-python
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from collections import deque
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse

from actions.browser_capture import _to_url

USER_AGENT = 'automa-pc'

_JS_ANCHORS = "els => els.map(e => ({text: (e.textContent || '').trim(), href: e.getAttribute('href')}))"
_JS_META = (
    "els => els.map(e => ({key: e.getAttribute('name') || e.getAttribute('property'),"
    " value: e.getAttribute('content') || ''}))"
)
_JS_TABLES = (
    'tables => tables.map(t => Array.from(t.rows).map(r =>'
    " Array.from(r.cells).map(c => (c.textContent || '').trim())))"
)


# ---------------------------------------------------------------------------
# Lógica pura (testeable sin Playwright)
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Colapsa espacios y líneas vacías repetidas para un hash estable."""
    lines = [line.strip() for line in (text or '').splitlines()]
    collapsed: list[str] = []
    for line in lines:
        if line or (collapsed and collapsed[-1]):
            collapsed.append(line)
    while collapsed and not collapsed[-1]:
        collapsed.pop()
    return '\n'.join(collapsed)


def content_hash(text: str) -> str:
    return hashlib.sha256((text or '').encode('utf-8')).hexdigest()


def parse_number(text: str | None) -> float | None:
    """Extrae un número de un texto tipo '$1,499.90' o '1.499,90 €'.

    Heurística documentada: si hay coma y punto, el separador más a la derecha
    es el decimal; con un solo separador y exactamente 3 dígitos detrás se
    asume separador de miles (salvo parte entera '0').
    """
    cleaned = re.sub(r'[^\d,.\-]', '', text or '')
    if not re.search(r'\d', cleaned):
        return None
    negative = cleaned.lstrip().startswith('-')
    cleaned = cleaned.replace('-', '')
    try:
        if ',' in cleaned and '.' in cleaned:
            dec = max(cleaned.rfind(','), cleaned.rfind('.'))
            int_part = re.sub(r'[,.]', '', cleaned[:dec])
            value = float(f'{int_part or 0}.{cleaned[dec + 1:] or 0}')
        elif ',' in cleaned or '.' in cleaned:
            sep = ',' if ',' in cleaned else '.'
            parts = cleaned.split(sep)
            if len(parts) == 2 and (len(parts[1]) != 3 or parts[0] in ('', '0')):
                value = float(f'{parts[0] or 0}.{parts[1] or 0}')
            else:
                value = float(''.join(parts))
        else:
            value = float(cleaned)
    except ValueError:
        return None
    return -value if negative else value


def resolve_links(
    anchors: list[dict[str, Any]],
    base_url: str,
    max_links: int = 200,
) -> tuple[list[dict[str, str]], bool]:
    """Convierte anchors crudos en links absolutos, únicos, en orden de aparición."""
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    truncated = False
    for anchor in anchors or []:
        href = (anchor.get('href') or '').strip()
        if not href or href.startswith('#'):
            continue
        if href.lower().startswith(('javascript:', 'data:')):
            continue
        if href.lower().startswith(('mailto:', 'tel:')):
            absolute = href
        else:
            absolute, _ = urldefrag(urljoin(base_url, href))
        if absolute in seen:
            continue
        if len(links) >= max_links:
            truncated = True
            break
        seen.add(absolute)
        links.append({'text': (anchor.get('text') or '')[:200], 'url': absolute})
    return links, truncated


def apply_tracking(state_path: str, url: str, watch_value: str) -> dict[str, Any]:
    """Compara ``watch_value`` contra la corrida anterior y persiste el estado.

    Mismo patrón de tracking persistente que ``data/seeds/.used_indices.json``
    del caso 07: el archivo de estado vive en ``data/``, no en ``state/``
    (que es de los run-states del orchestrator).
    """
    path = Path(state_path)
    previous: dict[str, Any] | None = None
    if path.exists():
        try:
            previous = json.loads(path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            previous = None
    first_run = previous is None
    previous_value = (previous or {}).get('watch_value')
    changed = (not first_run) and previous_value != watch_value
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                'url': url,
                'watch_value': watch_value,
                'checked_at': datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )
    return {
        'first_run': first_run,
        'changed': changed,
        'previous_value': previous_value,
        'state_path': str(path),
    }


def render_markdown(result: dict[str, Any]) -> str:
    """Serializa el contenido extraído como Markdown de archivo."""
    lines = [
        f"# {result.get('title') or result.get('url', '')}",
        '',
        f"> Fuente: {result.get('url', '')}",
        f"> SHA-256: {result.get('content_hash', '')}",
        f"> Capturado: {datetime.now(timezone.utc).isoformat()}",
        '',
    ]
    description = (result.get('meta') or {}).get('description')
    if description:
        lines.extend([f'_{description}_', ''])
    if result.get('text'):
        lines.extend(['## Contenido', '', result['text'], ''])
    tables = result.get('tables') or []
    for index, table in enumerate(tables, start=1):
        if not table:
            continue
        lines.append(f'## Tabla {index}')
        lines.append('')
        header, *rows = table
        lines.append('| ' + ' | '.join(header) + ' |')
        lines.append('|' + '---|' * len(header))
        for row in rows:
            lines.append('| ' + ' | '.join(row) + ' |')
        lines.append('')
    links = result.get('links') or []
    if links:
        lines.extend(['## Links', ''])
        lines.extend(f"- [{link['text'] or link['url']}]({link['url']})" for link in links)
        lines.append('')
    return '\n'.join(lines)


def save_tables_csv(tables: list[list[list[str]]], directory: str) -> list[str]:
    """Escribe cada tabla como ``table_NN.csv`` dentro de ``directory``."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for index, table in enumerate(tables or [], start=1):
        csv_path = target / f'table_{index:02d}.csv'
        with csv_path.open('w', encoding='utf-8', newline='') as fh:
            csv.writer(fh).writerows(table)
        written.append(str(csv_path))
    return written


def build_result(
    raw: dict[str, Any],
    url: str,
    selector: str | None = None,
    parse_number_flag: bool = False,
    include_tables: bool = False,
    max_links: int = 200,
    max_text_chars: int = 200_000,
    track_state_path: str | None = None,
    save_markdown_path: str | None = None,
    save_tables_dir: str | None = None,
) -> dict[str, Any]:
    """Post-procesa lo scrapeado: links, hash, tracking, markdown y CSV."""
    text = normalize_text(raw.get('body_text', ''))
    text_truncated = len(text) > max_text_chars
    if text_truncated:
        text = text[:max_text_chars]
    links, links_truncated = resolve_links(raw.get('anchors') or [], url, max_links=max_links)
    digest = content_hash(text)
    meta = {k: v for k, v in (raw.get('meta') or {}).items() if v}
    tables = raw.get('tables') or []

    result: dict[str, Any] = {
        'url': url,
        'title': raw.get('title', ''),
        'text': text,
        'text_chars': len(text),
        'text_truncated': text_truncated,
        'content_hash': digest,
        'links': links,
        'link_urls': [link['url'] for link in links],
        'links_count': len(links),
        'links_truncated': links_truncated,
        'meta': meta,
        'method': 'playwright',
    }

    if selector:
        selector_value = raw.get('selector_text')
        result['selector'] = selector
        result['selector_found'] = selector_value is not None
        result['selector_value'] = normalize_text(selector_value) if selector_value is not None else None
        if parse_number_flag:
            result['selector_number'] = parse_number(result['selector_value'])

    if include_tables:
        result['tables'] = tables
        result['tables_count'] = len(tables)
        if save_tables_dir:
            result['tables_csv_paths'] = save_tables_csv(tables, save_tables_dir)
            result['tables_dir'] = save_tables_dir

    if track_state_path:
        watch_value = result.get('selector_value') if selector else digest
        result.update(apply_tracking(track_state_path, url, str(watch_value)))

    if save_markdown_path:
        markdown_target = Path(save_markdown_path)
        markdown_target.parent.mkdir(parents=True, exist_ok=True)
        markdown_target.write_text(render_markdown(result), encoding='utf-8')
        result['markdown_path'] = str(markdown_target)

    return result


def crawl_pages(
    fetch_page: Callable[[str], dict[str, Any]],
    start_url: str,
    max_pages: int = 10,
    max_depth: int = 2,
    same_domain_only: bool = True,
    delay_seconds: float = 0.0,
    robots_check: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    """BFS acotado y determinista: links en orden de aparición, sin repetir."""
    max_pages = max(1, int(max_pages))
    max_depth = max(0, int(max_depth))
    base_netloc = urlparse(start_url).netloc
    queue: deque[tuple[str, int]] = deque([(start_url, 0)])
    seen: set[str] = {start_url}
    pages: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    robots_blocked: list[str] = []

    while queue and len(pages) < max_pages:
        url, depth = queue.popleft()
        if robots_check is not None and not robots_check(url):
            robots_blocked.append(url)
            continue
        try:
            raw = fetch_page(url)
        except Exception as exc:  # noqa: BLE001 — un link caído no debe abortar el crawl
            errors.append({'url': url, 'error': str(exc)})
            continue
        links, _ = resolve_links(raw.get('anchors') or [], url)
        text = normalize_text(raw.get('body_text', ''))
        pages.append(
            {
                'url': url,
                'depth': depth,
                'title': raw.get('title', ''),
                'links_count': len(links),
                'text_chars': len(text),
                'content_hash': content_hash(text),
            }
        )
        if depth < max_depth:
            for link in links:
                candidate = link['url']
                if candidate in seen:
                    continue
                if not candidate.lower().startswith(('http://', 'https://', 'file://')):
                    continue
                if same_domain_only and urlparse(candidate).netloc != base_netloc:
                    continue
                seen.add(candidate)
                queue.append((candidate, depth + 1))
        if delay_seconds > 0 and queue:
            time.sleep(delay_seconds)

    return {
        'start_url': start_url,
        'pages': pages,
        'pages_count': len(pages),
        'max_pages': max_pages,
        'max_depth': max_depth,
        'same_domain_only': same_domain_only,
        'truncated': bool(queue),
        'robots_blocked': robots_blocked,
        'errors': errors,
        'method': 'playwright',
    }


class RobotsCache:
    """Consulta robots.txt una vez por host. Sólo aplica a http(s).

    Si robots.txt no existe o no se puede leer, se permite el acceso pero se
    registra ``checked=False`` para reportarlo con honestidad.
    """

    def __init__(self, user_agent: str = USER_AGENT, timeout: float = 5.0) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self._parsers: dict[str, Any] = {}
        self.checked_hosts: dict[str, bool] = {}

    def allows(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return True
        host = f'{parsed.scheme}://{parsed.netloc}'
        if host not in self._parsers:
            self._parsers[host] = self._fetch(host)
        parser = self._parsers[host]
        if parser is None:
            return True
        return parser.can_fetch(self.user_agent, url)

    def _fetch(self, host: str) -> Any:
        from urllib import robotparser

        import requests

        try:
            response = requests.get(
                f'{host}/robots.txt',
                timeout=self.timeout,
                headers={'User-Agent': self.user_agent},
            )
        except requests.RequestException:
            self.checked_hosts[host] = False
            return None
        if response.status_code >= 400:
            self.checked_hosts[host] = True
            return None
        parser = robotparser.RobotFileParser()
        parser.parse(response.text.splitlines())
        self.checked_hosts[host] = True
        return parser


# ---------------------------------------------------------------------------
# Glue Playwright (scrape sobre una página viva o fake con la misma interfaz)
# ---------------------------------------------------------------------------

def scrape_page(page: Any, selector: str | None = None, include_tables: bool = False) -> dict[str, Any]:
    """Lee el DOM de una ``page`` Playwright (o fake con la misma interfaz)."""
    raw: dict[str, Any] = {
        'title': page.title(),
        'body_text': page.inner_text('body'),
        'anchors': page.eval_on_selector_all('a[href]', _JS_ANCHORS),
    }
    meta_entries = page.eval_on_selector_all('meta[name], meta[property]', _JS_META)
    raw['meta'] = {entry['key']: entry['value'] for entry in meta_entries if entry.get('key')}
    if include_tables:
        raw['tables'] = page.eval_on_selector_all('table', _JS_TABLES)
    if selector:
        element = page.query_selector(selector)
        raw['selector_text'] = element.inner_text() if element is not None else None
    return raw


def _import_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise RuntimeError(
            'playwright no está instalado. Ejecuta: '
            'pip install playwright && python -m playwright install chromium'
        ) from exc
    return sync_playwright


def extract_content(
    target: str,
    selector: str | None = None,
    parse_number: bool = False,
    include_tables: bool = False,
    max_links: int = 200,
    max_text_chars: int = 200_000,
    track_state_path: str | None = None,
    save_markdown_path: str | None = None,
    save_tables_dir: str | None = None,
    viewport_width: int = 1280,
    viewport_height: int = 800,
    wait_seconds: float = 1.0,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """Extrae contenido estructurado de una URL o archivo HTML local.

    Args:
        target: URL (``http://``, ``https://``, ``file://``) o ruta a un .html.
        selector: selector CSS opcional para leer un valor puntual.
        parse_number: si True, intenta convertir ``selector_value`` a número.
        include_tables: si True, extrae las tablas HTML como matrices de celdas.
        max_links / max_text_chars: cotas explícitas de la extracción.
        track_state_path: archivo JSON de tracking; al pasarlo, el resultado
            incluye ``first_run``/``changed``/``previous_value`` comparando
            contra la corrida anterior (hash del texto, o el valor del
            selector si se indicó uno).
        save_markdown_path: si se indica, escribe el contenido como Markdown.
        save_tables_dir: si se indica (junto a ``include_tables``), escribe
            cada tabla como CSV en ese directorio.

    Returns:
        dict JSON-serializable con url, title, text, content_hash, links,
        meta y los campos opcionales según parámetros.
    """
    sync_playwright = _import_playwright()
    url = _to_url(target)

    with sync_playwright() as p:  # pragma: no cover - requiere Chromium real
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                viewport={'width': int(viewport_width), 'height': int(viewport_height)},
                user_agent=USER_AGENT,
            )
            page = context.new_page()
            page.set_default_timeout(int(timeout_seconds * 1000))
            page.goto(url, wait_until='load')
            if wait_seconds > 0:
                page.wait_for_timeout(int(wait_seconds * 1000))
            raw = scrape_page(page, selector=selector, include_tables=include_tables)
        finally:
            browser.close()

    return build_result(
        raw,
        url,
        selector=selector,
        parse_number_flag=bool(parse_number),
        include_tables=bool(include_tables),
        max_links=int(max_links),
        max_text_chars=int(max_text_chars),
        track_state_path=track_state_path,
        save_markdown_path=save_markdown_path,
        save_tables_dir=save_tables_dir,
    )


def crawl_site(
    start_url: str,
    max_pages: int = 10,
    max_depth: int = 2,
    same_domain_only: bool = True,
    delay_seconds: float = 0.5,
    respect_robots: bool = True,
    viewport_width: int = 1280,
    viewport_height: int = 800,
    wait_seconds: float = 0.5,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """Recorre un sitio con BFS acotado y devuelve el inventario de páginas.

    Cotas explícitas SIEMPRE: ``max_pages`` y ``max_depth`` evitan el crawl
    abierto. Con ``respect_robots=True`` consulta robots.txt (sólo http/https)
    y reporta las URLs bloqueadas en ``robots_blocked``.
    """
    sync_playwright = _import_playwright()
    url = _to_url(start_url)
    robots = RobotsCache() if respect_robots else None

    with sync_playwright() as p:  # pragma: no cover - requiere Chromium real
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                viewport={'width': int(viewport_width), 'height': int(viewport_height)},
                user_agent=USER_AGENT,
            )
            def new_page():
                fresh = context.new_page()
                fresh.set_default_timeout(int(timeout_seconds * 1000))
                return fresh

            page = new_page()

            def fetch_page(page_url: str) -> dict[str, Any]:
                # Un goto fallido deja la página en estado de error que
                # interrumpe la navegación siguiente — se descarta la página
                # y se abre una limpia antes de propagar el error.
                nonlocal page
                try:
                    page.goto(page_url, wait_until='load')
                except Exception:
                    try:
                        page.close()
                    except Exception:  # pragma: no cover - cierre best-effort
                        pass
                    page = new_page()
                    raise
                if wait_seconds > 0:
                    page.wait_for_timeout(int(wait_seconds * 1000))
                return scrape_page(page)

            report = crawl_pages(
                fetch_page,
                url,
                max_pages=int(max_pages),
                max_depth=int(max_depth),
                same_domain_only=bool(same_domain_only),
                delay_seconds=float(delay_seconds),
                robots_check=robots.allows if robots else None,
            )
        finally:
            browser.close()

    report['respect_robots'] = bool(respect_robots)
    if robots:
        report['robots_checked_hosts'] = robots.checked_hosts
    return report
