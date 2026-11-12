import html
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

SOURCES_DIR = os.path.dirname(os.path.abspath(__file__))
LIVRABLES_DIR = os.path.dirname(SOURCES_DIR)

CSS = """
@page {
  size: A4;
  margin: 16mm 15mm 16mm 15mm;
}
* { box-sizing: border-box; }
body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  color: #0F172A;
  font-size: 10.2pt;
  line-height: 1.52;
  margin: 0;
}
h1 {
  font-size: 18pt;
  color: #0B2545;
  border-bottom: 3px solid #0284C7;
  padding-bottom: 8px;
  margin-top: 0;
}
h2 {
  font-size: 13.5pt;
  color: #0369A1;
  margin-top: 18px;
  margin-bottom: 8px;
  border-left: 4px solid #0284C7;
  padding-left: 9px;
  page-break-after: avoid;
}
h3 {
  font-size: 11.2pt;
  color: #1E293B;
  margin-top: 12px;
  margin-bottom: 5px;
  page-break-after: avoid;
}
p { margin: 6px 0 8px 0; }
ul, ol { margin: 5px 0 10px 0; padding-left: 20px; }
li { margin-bottom: 4px; }
code {
  font-family: 'Cascadia Mono', 'Consolas', monospace;
  font-size: 9pt;
  background: #F1F5F9;
  color: #0F172A;
  padding: 1px 4px;
  border-radius: 3px;
}
hr {
  border: none;
  border-top: 1px solid #CBD5E1;
  margin: 14px 0;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0 14px 0;
  font-size: 9.1pt;
  page-break-inside: avoid;
}
th {
  background: #0B2545;
  color: #FFFFFF;
  text-align: left;
  padding: 7px 8px;
  font-weight: 600;
}
td {
  border: 1px solid #CBD5E1;
  padding: 6px 8px;
  vertical-align: top;
}
tr:nth-child(even) td { background: #F8FAFC; }
img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 10px auto 14px auto;
  border-radius: 8px;
  border: 1px solid #CBD5E1;
  page-break-inside: avoid;
}
em { color: #475569; }
"""


def inline_md(text: str, base_dir: str) -> str:
    # Images ![alt](path)
    img_m = re.match(r"^!\[(.*?)\]\((.*?)\)$", text.strip())
    if img_m:
        alt = html.escape(img_m.group(1))
        rel = img_m.group(2)
        abs_p = os.path.abspath(os.path.join(base_dir, rel))
        uri = "file:///" + abs_p.replace("\\", "/")
        return f'<img src="{uri}" alt="{alt}" />'

    escaped = html.escape(text)
    code_spans = []

    def _stash_code(m):
        idx = len(code_spans)
        code_spans.append(f"<code>{m.group(1)}</code>")
        return f"\x00CODE{idx}\x00"

    escaped = re.sub(r"`([^`]+)`", _stash_code, escaped)
    # Links [label](url)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    # Bold **x**
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    # Italics *x*
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    for idx, val in enumerate(code_spans):
        escaped = escaped.replace(f"\x00CODE{idx}\x00", val)
    return escaped


def md_to_html(md_path: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(md_path))
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue
        if stripped == "---":
            out.append("<hr />")
            i += 1
            continue
        if stripped.startswith("# "):
            out.append(f"<h1>{inline_md(stripped[2:], base_dir)}</h1>")
            i += 1
            continue
        if stripped.startswith("## "):
            out.append(f"<h2>{inline_md(stripped[3:], base_dir)}</h2>")
            i += 1
            continue
        if stripped.startswith("### "):
            out.append(f"<h3>{inline_md(stripped[4:], base_dir)}</h3>")
            i += 1
            continue
        if stripped.startswith("!["):
            out.append(inline_md(stripped, base_dir))
            i += 1
            continue

        # Markdown Table
        if "|" in stripped and i + 1 < len(lines) and re.match(r"^\s*\|?[\s:\-|]+\|\s*$", lines[i + 1]):
            headers = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            th_html = "".join(f"<th>{inline_md(h, base_dir)}</th>" for h in headers)
            body_html = ""
            for r in rows:
                tds = "".join(f"<td>{inline_md(c, base_dir)}</td>" for c in r)
                body_html += f"<tr>{tds}</tr>"
            out.append(f"<table><thead><tr>{th_html}</tr></thead><tbody>{body_html}</tbody></table>")
            continue

        # Unordered list (* or -)
        if re.match(r"^[\*\-]\s+", stripped):
            out.append("<ul>")
            while i < len(lines) and lines[i].strip():
                cur = lines[i]
                cur_s = cur.strip()
                if re.match(r"^[\*\-]\s+", cur_s):
                    content = re.sub(r"^[\*\-]\s+", "", cur_s)
                    out.append(f"<li>{inline_md(content, base_dir)}</li>")
                    i += 1
                elif re.match(r"^\d+\.\s+", cur_s):
                    out.append("<ol>")
                    while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                        content = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                        out.append(f"<li>{inline_md(content, base_dir)}</li>")
                        i += 1
                    out.append("</ol>")
                else:
                    break
            out.append("</ul>")
            continue

        # Ordered list (1. ...)
        if re.match(r"^\d+\.\s+", stripped):
            out.append("<ol>")
            while i < len(lines) and lines[i].strip():
                cur_s = lines[i].strip()
                if re.match(r"^\d+\.\s+", cur_s):
                    content = re.sub(r"^\d+\.\s+", "", cur_s)
                    out.append(f"<li>{inline_md(content, base_dir)}</li>")
                    i += 1
                elif re.match(r"^[\*\-]\s+", cur_s):
                    content = re.sub(r"^[\*\-]\s+", "", cur_s)
                    out.append(f"<li style='margin-left:18px;list-style-type:disc'>{inline_md(content, base_dir)}</li>")
                    i += 1
                else:
                    break
            out.append("</ol>")
            continue

        out.append(f"<p>{inline_md(stripped, base_dir)}</p>")
        i += 1

    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(out)}</body></html>"


def build_pdfs():
    pairs = [
        ("RAPPORT_ARCHITECTURE_TECHNIQUE_PIPELINE.md", "RAPPORT_ARCHITECTURE_TECHNIQUE_PIPELINE.pdf"),
        ("LIEN_DEMO_VIDEO.md", "LIEN_DEMO_VIDEO.pdf"),
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for md_name, pdf_name in pairs:
            md_path = os.path.join(SOURCES_DIR, md_name)
            html_path = os.path.join(SOURCES_DIR, f"_tmp_{pdf_name}.html")
            pdf_path = os.path.join(LIVRABLES_DIR, pdf_name)
            html_str = md_to_html(md_path)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_str)
            page = browser.new_page()
            page.goto("file:///" + html_path.replace("\\", "/"), wait_until="networkidle")
            page.pdf(path=pdf_path, format="A4", print_background=True)
            page.close()
            if os.path.exists(html_path):
                os.remove(html_path)
            print(f"✅ PDF généré : {pdf_path}")
        browser.close()


if __name__ == "__main__":
    build_pdfs()

