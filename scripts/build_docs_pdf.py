#!/usr/bin/env python3
"""Genera la versión PDF de la documentación de sistema de Automa.

Fuente única: los Markdown de ``docs/system-documentation/``.
Salida:       un PDF por documento en ``docs/system-documentation/pdf/``,
              más un consolidado ``00-documentacion-completa.pdf``.

Los Markdown son la única fuente de verdad. Este script NO edita los ``.md``:
los lee, rasteriza sus diagramas Mermaid, los convierte a HTML con una hoja de
estilo pensada para papel y los renderiza a PDF. Si un documento cambia, basta
con volver a ejecutar el script.

Uso
---
    python scripts/build_docs_pdf.py                  # todos los documentos
    python scripts/build_docs_pdf.py --only 03        # solo los que empiecen por 03
    python scripts/build_docs_pdf.py --check          # solo comprueba dependencias
    python scripts/build_docs_pdf.py --no-consolidado # omite el PDF unificado

Requisitos
----------
    pip install markdown xhtml2pdf          # obligatorio
    npm i -g @mermaid-js/mermaid-cli        # opcional: rasteriza los diagramas

Decisiones de diseño (y sus costos)
-----------------------------------
* **Rasterizado de Mermaid con ``mmdc``.** Ningún motor de PDF de Python
  ejecuta JavaScript, así que un bloque ```mermaid``` no se renderiza solo.
  Cuando ``mmdc`` está disponible se genera un PNG por diagrama, cacheado por
  hash SHA-256 del código fuente en ``.tmp/mermaid-cache/`` — la segunda
  ejecución solo rehace lo que cambió. Si ``mmdc`` NO está, el diagrama
  **degrada al código fuente** en bloque monoespaciado con aviso visible, y el
  resumen final informa cuántos degradaron. Nunca se degrada en silencio.
* **Windows + Node >= 20.12.** ``mmdc`` se instala como ``.cmd`` y Node se
  niega a lanzarlo sin shell (endurecimiento por CVE-2024-27980). Por eso la
  invocación pasa por ``shell=True`` con los argumentos entrecomillados.
* **Versión y commit se leen del repositorio**, nunca se escriben a mano: la
  versión sale de ``pyproject.toml`` y el commit de ``.git/HEAD``. Una portada
  con números a mano queda obsoleta en el primer commit.
* Los enlaces relativos entre documentos (``03-architecture.md``) se conservan
  como texto; en el PDF no navegan a otro archivo.
"""

from __future__ import annotations

import argparse
import base64
import datetime as _dt
import hashlib
import html
import io
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ── Metadatos del sistema documentado ────────────────────────────────────────
SYSTEM_NAME = "Automa"
DOCS_DIRNAME = Path("docs") / "system-documentation"
PDF_DIRNAME = "pdf"
CACHE_DIRNAME = Path(".tmp") / "mermaid-cache"
CONSOLIDATED_NAME = "00-documentacion-completa.pdf"

# Un documento se considera "largo" —y por tanto merece índice propio— a partir
# de este número de encabezados de nivel 2.
TOC_MIN_H2 = 4

# Ancho en píxeles del PNG del diagrama. Un valor alto da nitidez al imprimir;
# el CSS lo reescala al ancho de página.
MERMAID_PNG_WIDTH = 1400


# ── Dependencias ─────────────────────────────────────────────────────────────
def _load_dependencies():
    """Importa markdown y xhtml2pdf, con un mensaje útil si faltan."""
    missing = []
    try:
        import markdown  # noqa: F401
    except ImportError:
        missing.append("markdown")
    try:
        from xhtml2pdf import pisa  # noqa: F401
    except ImportError:
        missing.append("xhtml2pdf")

    if missing:
        print(
            "Faltan dependencias: "
            + ", ".join(missing)
            + "\nInstalalas con:\n\n    pip install "
            + " ".join(missing)
            + "\n",
            file=sys.stderr,
        )
        return None, None

    import markdown
    from xhtml2pdf import pisa

    return markdown, pisa


def find_mmdc() -> str | None:
    """Ruta al CLI de Mermaid, o None si no está instalado.

    En Windows el ejecutable es ``mmdc.cmd``; ``shutil.which`` lo resuelve
    consultando PATHEXT, así que basta con buscar ``mmdc``.
    """
    return shutil.which("mmdc")


# ── Utilidades de repositorio ────────────────────────────────────────────────
def repo_root() -> Path:
    """Raíz del repositorio, deducida de la ubicación de este script."""
    return Path(__file__).resolve().parent.parent


def read_version(root: Path) -> str:
    """Versión declarada en ``pyproject.toml``. Fuente única de verdad."""
    manifest = root / "pyproject.toml"
    try:
        in_project = False
        for line in manifest.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("["):
                in_project = stripped == "[project]"
                continue
            if in_project:
                match = re.match(r'^version\s*=\s*"([^"]+)"', stripped)
                if match:
                    return match.group(1)
    except OSError:
        pass
    return "desconocida"


def read_commit(root: Path) -> str:
    """Commit corto analizado, leído de ``.git`` sin invocar git."""
    head = root / ".git" / "HEAD"
    try:
        content = head.read_text(encoding="utf-8").strip()
        if content.startswith("ref:"):
            ref = content.split(" ", 1)[1].strip()
            ref_file = root / ".git" / ref
            if ref_file.exists():
                sha = ref_file.read_text(encoding="utf-8").strip()
            else:  # ref empaquetada en packed-refs
                sha = ""
                packed = root / ".git" / "packed-refs"
                for line in packed.read_text(encoding="utf-8").splitlines():
                    if line.endswith(" " + ref):
                        sha = line.split(" ", 1)[0]
                        break
        else:
            sha = content
        return sha[:7] if sha else "desconocido"
    except OSError:
        return "desconocido"


def document_title(markdown_text: str, fallback: str) -> str:
    """Primer encabezado H1 del documento; si no hay, el nombre del archivo."""
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


# ── Rasterizado de diagramas Mermaid ─────────────────────────────────────────
MERMAID_BLOCK = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)


def render_mermaid_png(source: str, cache_dir: Path, mmdc: str) -> Path | None:
    """Rasteriza un diagrama a PNG, cacheando por hash del código fuente.

    Devuelve la ruta del PNG, o ``None`` si ``mmdc`` falló. Un fallo no aborta
    la generación: el diagrama degrada a código fuente y se informa al final.
    """
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    cache_dir.mkdir(parents=True, exist_ok=True)
    png_path = cache_dir / f"{digest}.png"
    if png_path.exists() and png_path.stat().st_size > 0:
        return png_path

    with tempfile.TemporaryDirectory() as tmp:
        mmd_path = Path(tmp) / "diagram.mmd"
        # LF explícito: mmdc lee el fichero línea a línea y un CRLF de más
        # rompe el parseo de algunos diagramas.
        mmd_path.write_text(source + "\n", encoding="utf-8", newline="\n")
        # shell=True obligatorio en Windows: mmdc es un .cmd y Node >= 20.12
        # se niega a lanzarlo sin shell (CVE-2024-27980).
        command = (
            f'"{mmdc}" -i "{mmd_path}" -o "{png_path}" '
            f"-b white -w {MERMAID_PNG_WIDTH} -s 2"
        )
        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=120
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if proc.returncode != 0 or not png_path.exists() or png_path.stat().st_size == 0:
            return None
    return png_path


def png_data_uri(png_path: Path) -> str | None:
    """Devuelve el PNG como data URI base64, o None si no se puede leer.

    xhtml2pdf **no resuelve fiablemente URIs ``file:///`` en Windows**: emite
    "Could not get image data from src attribute" y deja el hueco vacío sin
    fallar, que es justo la degradación silenciosa que este script debe evitar.
    Embeber los bytes en la propia etiqueta elimina el problema de raíz, a costa
    de aumentar el tamaño del HTML intermedio (los PDF resultantes son de decenas
    o cientos de KB, muy por debajo de cualquier límite práctico).
    """
    try:
        raw = png_path.read_bytes()
    except OSError:
        return None
    if not raw:
        return None
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def replace_mermaid_blocks(
    text: str, cache_dir: Path, mmdc: str | None
) -> tuple[str, dict[str, str], int, int]:
    """Sustituye los bloques ```mermaid``` por marcadores opacos al Markdown.

    Devuelve ``(texto, marcadores, rasterizados, degradados)``. Los marcadores
    se restauran como HTML DESPUÉS de convertir el Markdown, para que el
    conversor no toque su contenido.
    """
    markers: dict[str, str] = {}
    rendered = 0
    degraded = 0
    counter = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal rendered, degraded, counter
        counter += 1
        source = match.group(1).rstrip()
        token = f"MERMAIDBLOCK{counter:03d}ENDMERMAID"

        png = render_mermaid_png(source, cache_dir, mmdc) if mmdc else None
        data_uri = png_data_uri(png) if png is not None else None
        if data_uri is not None:
            rendered += 1
            markers[token] = (
                '<div class="diagram">'
                f'<img src="{data_uri}" class="diagram-img" alt="Diagrama {counter}" />'
                f'<p class="diagram-label">Diagrama {counter} (Mermaid, renderizado)</p>'
                "</div>"
            )
        else:
            degraded += 1
            markers[token] = (
                '<div class="diagram">'
                f'<p class="diagram-label">Diagrama {counter} — codigo fuente Mermaid '
                "(no renderizado: mermaid-cli no disponible o el rasterizado fallo)</p>"
                f'<pre class="diagram-code">{html.escape(source)}</pre>'
                "</div>"
            )
        return f"\n\n{token}\n\n"

    return MERMAID_BLOCK.sub(_replace, text), markers, rendered, degraded


def build_toc(markdown_text: str) -> str:
    """Índice de los encabezados H2 del documento, o cadena vacía si es corto."""
    headings = [
        line[3:].strip()
        for line in markdown_text.splitlines()
        if line.startswith("## ")
    ]
    if len(headings) < TOC_MIN_H2:
        return ""
    # Los encabezados ya llevan su propia numeración ("1. Motor y ubicación"),
    # así que el índice NO debe añadir otra: se emite como párrafos.
    items = "\n".join(f'<p class="toc-item">{html.escape(h)}</p>' for h in headings)
    return (
        '<div class="toc">\n<p class="toc-title">Contenido de este documento</p>\n'
        f"{items}\n</div>\n<pdf:nextpage />\n"
    )


# ── Plantilla y estilos ──────────────────────────────────────────────────────
# Estilos pensados para papel: cuerpo compacto, tablas que no desbordan, código
# legible en monoespaciada. xhtml2pdf soporta un subconjunto de CSS 2.1.
STYLESHEET = """
@page {
    size: a4 portrait;
    margin: 1.9cm 1.6cm 2.1cm 1.6cm;
    @frame footer { -pdf-frame-content: footer; bottom: 1.0cm; margin-left: 1.6cm;
                    margin-right: 1.6cm; height: 1cm; }
}
body { font-family: Helvetica, Arial, sans-serif; font-size: 8.6pt; line-height: 1.42;
       color: #1a1a1a; }
h1 { font-size: 17pt; color: #0f766e; margin: 0 0 4pt 0; border-bottom: 1.6pt solid #14b8a6;
     padding-bottom: 4pt; }
h2 { font-size: 12pt; color: #0f766e; margin: 15pt 0 5pt 0; border-bottom: 0.6pt solid #c2e7e1;
     padding-bottom: 2pt; }
h3 { font-size: 10pt; color: #115e59; margin: 11pt 0 4pt 0; }
h4 { font-size: 9pt; color: #115e59; margin: 9pt 0 3pt 0; }
p { margin: 0 0 5pt 0; text-align: left; }
ul, ol { margin: 0 0 6pt 14pt; padding: 0; }
li { margin: 0 0 2pt 0; }
a { color: #0f766e; text-decoration: none; }
code { font-family: Courier, monospace; font-size: 8pt; background-color: #f1f5f4;
       color: #9a3412; word-wrap: break-word; }
/* En tablas el ancho es escaso: el codigo debe partir palabra si hace falta,
   o una ruta larga como la de LOCALAPPDATA invade la celda vecina. */
td code, th code { font-size: 6.8pt; word-wrap: break-word; }
pre { font-family: Courier, monospace; font-size: 7.2pt; background-color: #f6f8f8;
      border: 0.5pt solid #d7e2e0; border-left: 2.4pt solid #14b8a6; padding: 5pt;
      margin: 5pt 0 7pt 0; line-height: 1.28; }
pre code { background-color: transparent; color: #24292f; }
blockquote { border-left: 2.4pt solid #d29922; background-color: #fffaf0; padding: 5pt 7pt;
             margin: 5pt 0 7pt 0; color: #4a3c14; }
blockquote p { margin: 0; }
table { border-collapse: collapse; width: 100%; margin: 5pt 0 8pt 0; font-size: 7.2pt; }
/* Tablas de mas de 6 columnas (la matriz de trazabilidad llega a 10): el ancho
   por columna baja de 1,5 cm y cualquier identificador largo invade la celda
   vecina. Se reduce el cuerpo y se fuerza el corte por caracter con la
   extension -pdf-word-wrap de xhtml2pdf, que es la unica forma de partir un
   token sin espacios como `filesystem.classify_file_inventory`. */
table.wide { font-size: 5.6pt; }
table.wide th, table.wide td { padding: 2pt 2.4pt; -pdf-word-wrap: CJK; }
table.wide code { font-size: 5.4pt; }
th { background-color: #0f766e; color: #ffffff; border: 0.5pt solid #0f766e; padding: 3.2pt 4pt;
     text-align: left; font-weight: bold; }
td { border: 0.5pt solid #c2e7e1; padding: 3.2pt 4pt; vertical-align: top;
     word-wrap: break-word; overflow: hidden; }
hr { border: none; border-top: 0.5pt solid #c2e7e1; margin: 10pt 0; }
.cover { text-align: center; padding-top: 2.4cm; }
.cover-system { font-size: 12pt; color: #14b8a6; letter-spacing: 1.2pt; margin-bottom: 6pt;
                text-align: center; }
.cover-title { font-size: 22pt; color: #0f766e; font-weight: bold; margin: 10pt 2.0cm 14pt 2.0cm;
               line-height: 1.2; text-align: center; }
.cover-rule { border-top: 1.6pt solid #14b8a6; width: 42%; margin: 0 auto 14pt auto; }
.cover-meta { font-size: 9.5pt; color: #444444; line-height: 1.8; text-align: center; }
.cover-note { font-size: 7.6pt; color: #777777; margin-top: 1.3cm; text-align: center; }
.toc { margin-top: 10pt; }
.toc-title { font-size: 11pt; color: #0f766e; font-weight: bold; border-bottom: 0.6pt solid #c2e7e1;
             padding-bottom: 3pt; }
.toc-item { margin: 0 0 3.5pt 12pt; font-size: 8.8pt; color: #24292f; }
.diagram { margin: 6pt 0 9pt 0; text-align: center; }
.diagram-img { width: 15.5cm; }
.diagram-label { font-size: 7.4pt; color: #6a737d; font-style: italic; margin: 2pt 0 0 0; }
.diagram-code { font-family: Courier, monospace; font-size: 6.9pt; background-color: #f6f8f8;
                border: 0.5pt dashed #a8bcb8; padding: 5pt; line-height: 1.25; text-align: left; }
.docsep { border-top: 1.2pt solid #14b8a6; margin: 0 0 8pt 0; }
#footer { font-size: 7pt; color: #8a8a8a; text-align: center; }
"""

PAGE_TEMPLATE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8" /><title>{title}</title>
<style>{stylesheet}</style></head>
<body>
<div id="footer">{system} &middot; {title} &middot; v{version} &middot; {date}
&middot; pag. <pdf:pagenumber /> de <pdf:pagecount /></div>
<div class="cover">
  <p class="cover-system">{system}</p>
  <p class="cover-title">{title}</p>
  <div class="cover-rule"></div>
  <p class="cover-meta">
    Documentacion del sistema<br />
    Version analizada: <b>{version}</b><br />
    Commit analizado: <b>{commit}</b><br />
    Fecha de generacion: <b>{date}</b>
  </p>
  <p class="cover-note">
    Generado a partir de {source} &mdash; los Markdown son la fuente unica.<br />
    No editar este PDF: editar el Markdown y regenerar.
  </p>
</div>
<pdf:nextpage />
{toc}
{content}
</body>
</html>
"""

MD_EXTENSIONS = ["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html"]

# Los emoji no existen en las fuentes base de PDF (Helvetica, Courier): xhtml2pdf
# los pinta como un cuadro negro. Se sustituyen por marcadores ASCII legibles
# SOLO al generar el PDF — el Markdown, que es la fuente unica y se lee en
# GitHub, conserva los emoji originales.
EMOJI_FALLBACK = {
    "✅": "[OK]",
    "❌": "[NO]",
    "⚠️": "[!]",
    "⚠": "[!]",
    "🔴": "[alto]",
    "🟠": "[medio]",
    "🟡": "[bajo]",
    "🟢": "[ok]",
    "🔵": "[info]",
    "🔷": "[propio]",
    "🔬": "[manual]",
    "○": "o",
}

# Un <table> con mas de este numero de columnas se marca como "wide".
WIDE_TABLE_COLS = 6

_THEAD_ROW = re.compile(r"<thead>.*?<tr>(.*?)</tr>", re.DOTALL)


def postprocess_html(html_body: str) -> str:
    """Marca las tablas anchas y degrada los emoji a marcadores ASCII."""
    for emoji, replacement in EMOJI_FALLBACK.items():
        html_body = html_body.replace(emoji, replacement)

    out: list[str] = []
    for chunk in re.split(r"(<table>)", html_body):
        if chunk != "<table>":
            out.append(chunk)
            continue
        out.append("<table>")
    html_body = "".join(out)

    # Recorremos cada <table>...</table> y contamos sus <th>.
    pieces = []
    pos = 0
    for match in re.finditer(r"<table>(.*?)</table>", html_body, re.DOTALL):
        head = _THEAD_ROW.search(match.group(1))
        cols = head.group(1).count("<th") if head else 0
        pieces.append(html_body[pos:match.start()])
        tag = '<table class="wide">' if cols > WIDE_TABLE_COLS else "<table>"
        pieces.append(tag + match.group(1) + "</table>")
        pos = match.end()
    pieces.append(html_body[pos:])
    return "".join(pieces)



def markdown_to_body(
    md_module, md_path: Path, cache_dir: Path, mmdc: str | None, drop_h1: bool
) -> tuple[str, int, int]:
    """Convierte un Markdown a HTML de cuerpo, con los diagramas resueltos."""
    raw = md_path.read_text(encoding="utf-8")
    body_md, markers, rendered, degraded = replace_mermaid_blocks(raw, cache_dir, mmdc)
    if drop_h1:
        # El H1 ya aparece en la portada; quitarlo del cuerpo evita duplicarlo.
        body_md = re.sub(r"^# .*?\n", "", body_md, count=1)
    html_body = md_module.markdown(body_md, extensions=MD_EXTENSIONS)
    html_body = postprocess_html(html_body)
    for token, replacement in markers.items():
        # El conversor envuelve el marcador suelto en un <p>; se sustituye
        # el párrafo entero para no dejar un <p> vacío alrededor de un <div>.
        html_body = html_body.replace(f"<p>{token}</p>", replacement)
        html_body = html_body.replace(token, replacement)
    return html_body, rendered, degraded


def write_pdf(pisa_module, document: str, out_path: Path) -> str:
    """Renderiza el HTML a PDF. Devuelve '' si todo fue bien, o el error."""
    buffer = io.BytesIO()
    # show_error_as_pdf=False: preferimos fallar y avisar antes que generar un
    # PDF cuyo contenido sea el mensaje de error.
    status = pisa_module.CreatePDF(
        io.StringIO(document), dest=buffer, encoding="utf-8", show_error_as_pdf=False
    )
    if status.err:
        return f"xhtml2pdf devolvio {status.err} error(es)"
    data = buffer.getvalue()
    if not data:
        return "xhtml2pdf produjo un PDF vacio"
    out_path.write_bytes(data)
    if out_path.stat().st_size == 0:
        return "el PDF resultante tiene 0 bytes"
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genera los PDF de docs/system-documentation/ a partir de los Markdown."
    )
    parser.add_argument(
        "--only",
        action="append",
        default=None,
        help="Prefijo de archivo a generar (p. ej. --only 03). Repetible.",
    )
    parser.add_argument("--out", default=None, help="Directorio de salida alternativo.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Solo comprueba dependencias y archivos, sin generar nada.",
    )
    parser.add_argument(
        "--no-consolidado",
        action="store_true",
        help="No generar el PDF unificado con todos los documentos.",
    )
    args = parser.parse_args()

    root = repo_root()
    docs_dir = root / DOCS_DIRNAME
    out_dir = Path(args.out) if args.out else docs_dir / PDF_DIRNAME
    cache_dir = root / CACHE_DIRNAME

    if not docs_dir.is_dir():
        print(f"No existe el directorio de documentacion: {docs_dir}", file=sys.stderr)
        return 1

    # Orden: portada primero, luego numéricos.
    all_md = sorted(docs_dir.glob("*.md"))
    sources = [p for p in all_md if p.stem == "README"] + [
        p for p in all_md if p.stem != "README"
    ]
    if args.only:
        sources = [p for p in sources if any(p.name.startswith(f) for f in args.only)]

    if not sources:
        print("No hay documentos que generar con esos filtros.", file=sys.stderr)
        return 1

    md_module, pisa_module = _load_dependencies()
    if md_module is None:
        return 1

    mmdc = find_mmdc()
    version = read_version(root)
    commit = read_commit(root)
    today = _dt.date.today().isoformat()

    if args.check:
        print("Dependencias disponibles: markdown, xhtml2pdf")
        print(f"mermaid-cli (mmdc): {mmdc or 'NO DISPONIBLE (los diagramas degradaran)'}")
        print(f"Documentos detectados: {len(sources)}")
        print(f"Version: {version}  -  Commit: {commit}")
        print(f"Salida: {out_dir}")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generando PDF - {SYSTEM_NAME} v{version} - commit {commit}")
    print(f"mermaid-cli: {mmdc or 'NO DISPONIBLE'}")
    print(f"Salida: {out_dir}\n")

    generated, failed = 0, []
    total_rendered, total_degraded = 0, 0
    consolidated_parts: list[str] = []

    for md_path in sources:
        raw = md_path.read_text(encoding="utf-8")
        title = document_title(raw, md_path.stem)
        body_html, rendered, degraded = markdown_to_body(
            md_module, md_path, cache_dir, mmdc, drop_h1=True
        )
        total_rendered += rendered
        total_degraded += degraded

        stripped_md = re.sub(r"^# .*?\n", "", raw, count=1)
        document = PAGE_TEMPLATE.format(
            title=html.escape(title),
            system=html.escape(SYSTEM_NAME),
            version=html.escape(version),
            commit=html.escape(commit),
            date=html.escape(today),
            source=html.escape(md_path.name),
            stylesheet=STYLESHEET,
            toc=build_toc(stripped_md),
            content=body_html,
        )

        out_path = out_dir / (md_path.stem + ".pdf")
        error = write_pdf(pisa_module, document, out_path)
        if error:
            print(f"  FALLO {out_path.name:<44} {error}", file=sys.stderr)
            failed.append(md_path.name)
        else:
            size_kb = out_path.stat().st_size / 1024
            extra = ""
            if rendered or degraded:
                extra = f"  [{rendered} diagrama(s) PNG, {degraded} degradado(s)]"
            print(f"  OK    {out_path.name:<44} {size_kb:7.1f} KB{extra}")
            generated += 1

        consolidated_parts.append(
            f'<h1>{html.escape(title)}</h1>\n<div class="docsep"></div>\n{body_html}'
        )

    if not args.no_consolidado and not args.only and consolidated_parts:
        joined = "\n<pdf:nextpage />\n".join(consolidated_parts)
        document = PAGE_TEMPLATE.format(
            title="Documentacion completa del sistema",
            system=html.escape(SYSTEM_NAME),
            version=html.escape(version),
            commit=html.escape(commit),
            date=html.escape(today),
            source=f"los {len(sources)} Markdown de docs/system-documentation/",
            stylesheet=STYLESHEET,
            toc="",
            content=joined,
        )
        out_path = out_dir / CONSOLIDATED_NAME
        error = write_pdf(pisa_module, document, out_path)
        if error:
            print(f"  FALLO {out_path.name:<44} {error}", file=sys.stderr)
            failed.append(CONSOLIDATED_NAME)
        else:
            size_kb = out_path.stat().st_size / 1024
            print(f"  OK    {out_path.name:<44} {size_kb:7.1f} KB  [consolidado]")
            generated += 1

    print(f"\n{generated} PDF generado(s) en {out_dir}")
    print(f"Diagramas Mermaid: {total_rendered} rasterizado(s) a PNG, {total_degraded} degradado(s) a codigo fuente.")
    if total_degraded:
        print(
            "AVISO: hay diagramas sin renderizar. Instala mermaid-cli para incluirlos "
            "como imagen:  npm i -g @mermaid-js/mermaid-cli",
            file=sys.stderr,
        )
    if failed:
        print(f"{len(failed)} fallo(s): {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
