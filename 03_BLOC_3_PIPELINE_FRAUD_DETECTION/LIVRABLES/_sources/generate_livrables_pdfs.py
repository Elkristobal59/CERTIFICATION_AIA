# -*- coding: utf-8 -*-
"""
Compile les livrables Markdown du Bloc 3 en PDF propres (style sobre & lisible),
avec rendu Chromium Playwright et pied de page Page X / Y.
"""
import base64
import os
import pathlib
import re
import sys
import markdown
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOURCES_DIR = pathlib.Path(__file__).resolve().parent
LIVRABLES_DIR = SOURCES_DIR.parent

CSS = """
@page {
    size: A4 portrait;
    margin: 13mm 14mm 14mm 14mm;
}
* { box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Segoe UI Emoji", Helvetica, Arial, sans-serif;
    font-size: 9.7pt;
    line-height: 1.50;
    color: #1f2328;
    margin: 0;
    padding: 0;
}
h1 {
    font-size: 16.5pt;
    font-weight: 700;
    color: #0f172a;
    border-bottom: 1.5px solid #d0d7de;
    padding-bottom: 6px;
    margin-top: 0;
    margin-bottom: 10px;
    break-after: avoid;
}
h2 {
    font-size: 12.8pt;
    font-weight: 700;
    color: #0f172a;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 4px;
    margin-top: 15px;
    margin-bottom: 8px;
    break-after: avoid;
}
h3 {
    font-size: 10.6pt;
    font-weight: 600;
    color: #1e293b;
    margin-top: 10px;
    margin-bottom: 5px;
    break-after: avoid;
}
p { margin: 5px 0 8px 0; }
blockquote {
    margin: 6px 0 10px 0;
    padding: 7px 12px;
    background: #f6f8fa;
    border-left: 3.5px solid #0969da;
    color: #334155;
    border-radius: 3px;
}
blockquote p { margin: 2px 0; }
ul, ol { margin: 4px 0 8px 0; padding-left: 22px; }
li { margin: 3px 0; }
hr {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 12px 0;
}
code {
    font-family: "Cascadia Mono", Consolas, "Courier New", monospace;
    font-size: 8.6pt;
    background: #f1f5f9;
    padding: 1px 4px;
    border-radius: 3px;
    color: #0f172a;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0 12px 0;
    font-size: 8.8pt;
    page-break-inside: avoid;
}
th, td {
    border: 1px solid #d0d7de;
    padding: 5px 6.5px;
    text-align: left;
    vertical-align: top;
}
th {
    background: #f6f8fa;
    color: #0f172a;
    font-weight: 600;
    white-space: nowrap;
}
tr:nth-child(even) td { background: #fbfcfd; }
img {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 8px auto 10px auto;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    page-break-inside: avoid;
}
a { color: #0969da; text-decoration: none; }
"""


def inline_local_images(html_body: str, base_dir: pathlib.Path) -> str:
    def _repl(match):
        prefix, rel_src, suffix = match.group(1), match.group(2), match.group(3)
        if rel_src.startswith(("http://", "https://", "data:")):
            return match.group(0)
        img_path = (base_dir / rel_src).resolve()
        if not img_path.exists():
            raise FileNotFoundError(f"Missing image in Markdown: {img_path}")
        b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
        ext = img_path.suffix.lstrip(".").lower() or "png"
        return f"{prefix}data:image/{ext};base64,{b64}{suffix}"

    return re.sub(r'(<img\b[^>]*?\ssrc=")([^"]+)(")', _repl, html_body)


def build_pdfs() -> None:
    pairs = [
        ("RAPPORT_ARCHITECTURE_TECHNIQUE_PIPELINE.md", "RAPPORT_ARCHITECTURE_TECHNIQUE_PIPELINE.pdf"),
        ("LIEN_DEMO_VIDEO.md", "LIEN_DEMO_VIDEO.pdf"),
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for md_name, pdf_name in pairs:
            md_path = SOURCES_DIR / md_name
            pdf_path = LIVRABLES_DIR / pdf_name
            md_text = md_path.read_text(encoding="utf-8")
            body_html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
            body_html = inline_local_images(body_html, SOURCES_DIR)
            full_html = (
                f'<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
                f"<style>{CSS}</style></head><body>{body_html}</body></html>"
            )
            page = browser.new_page()
            page.set_content(full_html, wait_until="load")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                display_header_footer=True,
                header_template="<div></div>",
                footer_template=(
                    '<div style="width:100%;text-align:center;font-size:8pt;color:#64748b;'
                    'font-family:Segoe UI,Arial,sans-serif;">'
                    f'{pdf_name.replace(".pdf", "")} · Page <span class="pageNumber"></span> / <span class="totalPages"></span>'
                    "</div>"
                ),
                margin={"top": "13mm", "right": "14mm", "bottom": "14mm", "left": "14mm"},
            )
            page.close()
            print(f"[OK] PDF genere : {pdf_path} ({pdf_path.stat().st_size:,} B)")
        browser.close()


if __name__ == "__main__":
    build_pdfs()
