# -*- coding: utf-8 -*-
"""
Genere le schema d'architecture deployee Bloc 3 (Detection de Fraude Bancaire)
au format natif Draw.io (.drawio) + PNG haute resolution (2x via Chromium SVG),
strictement aligne sur le style visuel Draw.io du Bloc 2.
"""
import html
import math
import pathlib
import sys
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOURCES_DIR = pathlib.Path(__file__).resolve().parent
LIVRABLES_DIR = SOURCES_DIR.parent
OUT_DRAWIO = SOURCES_DIR / "schema_architecture_infrastructure_fraud.drawio"
OUT_PNG = LIVRABLES_DIR / "schema_architecture_infrastructure_fraud.png"

COLORS = {
    "zone": ("#F5F5F5", "#666666"),
    "blue": ("#DAE8FC", "#6C8EBF"),
    "green": ("#D5E8D4", "#82B366"),
    "yellow": ("#FFF2CC", "#D6B656"),
    "orange": ("#FFE6CC", "#D79B00"),
    "red": ("#F8CECC", "#B85450"),
    "violet": ("#E1D5E7", "#9673A6"),
}


class DrawioDiagram:
    def __init__(self, name: str, title: str, width: int, height: int):
        self.name = name
        self.title = title
        self.width = width
        self.height = height
        self.nodes = []
        self.edges = []
        self._id_counter = 2

    def _next_id(self) -> str:
        val = f"n{self._id_counter}"
        self._id_counter += 1
        return val

    def add_zone(self, key: str, x: int, y: int, w: int, h: int, label: str, align: str = "left"):
        self.nodes.append({
            "key": key,
            "id": self._next_id(),
            "kind": "zone",
            "x": x, "y": y, "w": w, "h": h,
            "label": label,
            "align": align,
            "color": "zone",
        })

    def add_box(self, key: str, x: int, y: int, w: int, h: int, title: str, subtitle: str = "", color: str = "blue"):
        self.nodes.append({
            "key": key,
            "id": self._next_id(),
            "kind": "box",
            "x": x, "y": y, "w": w, "h": h,
            "title": title,
            "subtitle": subtitle,
            "color": color,
        })

    def add_edge(
        self,
        src: str,
        dst: str,
        label: str = "",
        exit_side: str = "right",
        entry_side: str = "left",
        exit_pos: float = 0.5,
        entry_pos: float = 0.5,
        waypoints=None,
        dashed: bool = False,
        bidir: bool = False,
        label_pos=None,
        color: str = "#555555",
    ):
        self.edges.append({
            "id": self._next_id(),
            "src": src,
            "dst": dst,
            "label": label,
            "exit_side": exit_side,
            "entry_side": entry_side,
            "exit_pos": exit_pos,
            "entry_pos": entry_pos,
            "waypoints": waypoints or [],
            "dashed": dashed,
            "bidir": bidir,
            "label_pos": label_pos,
            "color": color,
        })

    def _node_by_key(self, key: str):
        for n in self.nodes:
            if n["key"] == key:
                return n
        raise KeyError(f"Unknown node key: {key}")

    @staticmethod
    def _side_coords(side: str, pos: float):
        if side == "left":
            return 0, pos
        if side == "right":
            return 1, pos
        if side == "top":
            return pos, 0
        if side == "bottom":
            return pos, 1
        raise ValueError(side)

    def _port_xy(self, key: str, side: str, pos: float):
        n = self._node_by_key(key)
        rx, ry = self._side_coords(side, pos)
        return n["x"] + n["w"] * rx, n["y"] + n["h"] * ry

    def to_drawio_xml(self) -> str:
        mxfile = ET.Element("mxfile", host="app.diagrams.net")
        diagram = ET.SubElement(mxfile, "diagram", name=self.name)
        model = ET.SubElement(
            diagram, "mxGraphModel",
            dx="1200", dy="800", grid="1", gridSize="10",
            page="1", pageWidth=str(self.width), pageHeight=str(self.height),
        )
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")

        t_cell = ET.SubElement(
            root, "mxCell",
            id=self._next_id(),
            value=self.title,
            style="text;html=1;align=center;verticalAlign=middle;fontSize=18;fontColor=#222222;fontStyle=1;",
            vertex="1", parent="1",
        )
        ET.SubElement(
            t_cell, "mxGeometry",
            x="40", y="16", width=str(self.width - 80), height="30",
            **{"as": "geometry"},
        )

        for n in self.nodes:
            fill, stroke = COLORS[n["color"]]
            if n["kind"] == "zone":
                align = n.get("align", "left")
                style = (
                    f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};"
                    f"strokeColor={stroke};fontSize=13;fontStyle=1;align={align};verticalAlign=top;spacingTop=8;spacingLeft=12;"
                )
                val = n["label"]
            else:
                style = (
                    f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};"
                    f"strokeColor={stroke};fontSize=12;verticalAlign=middle;"
                )
                if n["subtitle"]:
                    val = f"<b>{html.escape(n['title'])}</b><br/><font style='font-size:10px;color:#475569'>{html.escape(n['subtitle'])}</font>"
                else:
                    val = f"<b>{html.escape(n['title'])}</b>"
            cell = ET.SubElement(
                root, "mxCell",
                id=n["id"], value=val, style=style, vertex="1", parent="1",
            )
            ET.SubElement(
                cell, "mxGeometry",
                x=str(n["x"]), y=str(n["y"]), width=str(n["w"]), height=str(n["h"]),
                **{"as": "geometry"},
            )

        for e in self.edges:
            sn = self._node_by_key(e["src"])
            tn = self._node_by_key(e["dst"])
            ex, ey = self._side_coords(e["exit_side"], e["exit_pos"])
            nx, ny = self._side_coords(e["entry_side"], e["entry_pos"])
            style = (
                f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;"
                f"strokeColor={e['color']};strokeWidth=2;fontSize=10;"
                f"exitX={ex};exitY={ey};entryX={nx};entryY={ny};"
                f"exitDx=0;exitDy=0;entryDx=0;entryDy=0;"
            )
            if e["dashed"]:
                style += "dashed=1;"
            if e["bidir"]:
                style += "startArrow=classic;endArrow=classic;"
            cell = ET.SubElement(
                root, "mxCell",
                id=e["id"], value=e["label"], style=style,
                edge="1", parent="1", source=sn["id"], target=tn["id"],
            )
            geom = ET.SubElement(cell, "mxGeometry", relative="1", **{"as": "geometry"})
            if e["waypoints"]:
                arr = ET.SubElement(geom, "Array", **{"as": "points"})
                for px, py in e["waypoints"]:
                    ET.SubElement(arr, "mxPoint", x=str(px), y=str(py))

        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(mxfile, encoding="unicode")

    @staticmethod
    def _wrap_text(text: str, max_chars: int):
        words = text.split()
        lines, cur = [], ""
        for w in words:
            if not cur:
                cur = w
            elif len(cur) + 1 + len(w) <= max_chars:
                cur += " " + w
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    @staticmethod
    def _rounded_orthogonal_path(pts, r=8):
        if len(pts) < 2:
            return ""
        if len(pts) == 2:
            return f"M {pts[0][0]:.1f} {pts[0][1]:.1f} L {pts[1][0]:.1f} {pts[1][1]:.1f}"
        d = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
        for i in range(1, len(pts) - 1):
            p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
            dx1, dy1 = p1[0] - p0[0], p1[1] - p0[1]
            dx2, dy2 = p2[0] - p1[0], p2[1] - p1[1]
            l1 = math.hypot(dx1, dy1)
            l2 = math.hypot(dx2, dy2)
            if l1 < 1e-3 or l2 < 1e-3:
                d.append(f"L {p1[0]:.1f} {p1[1]:.1f}")
                continue
            cr = min(r, l1 / 2.0, l2 / 2.0)
            ax = p1[0] - (dx1 / l1) * cr
            ay = p1[1] - (dy1 / l1) * cr
            bx = p1[0] + (dx2 / l2) * cr
            by = p1[1] + (dy2 / l2) * cr
            d.append(f"L {ax:.1f} {ay:.1f} Q {p1[0]:.1f} {p1[1]:.1f} {bx:.1f} {by:.1f}")
        d.append(f"L {pts[-1][0]:.1f} {pts[-1][1]:.1f}")
        return " ".join(d)

    def _compute_orthogonal_pts(self, e):
        x1, y1 = self._port_xy(e["src"], e["exit_side"], e["exit_pos"])
        x2, y2 = self._port_xy(e["dst"], e["entry_side"], e["entry_pos"])
        if e["waypoints"]:
            pts = [(x1, y1)] + list(e["waypoints"]) + [(x2, y2)]
        else:
            if e["exit_side"] in ("left", "right") and e["entry_side"] in ("left", "right"):
                if abs(y1 - y2) < 1.5:
                    pts = [(x1, y1), (x2, y2)]
                else:
                    mx = (x1 + x2) / 2.0
                    pts = [(x1, y1), (mx, y1), (mx, y2), (x2, y2)]
            elif e["exit_side"] in ("top", "bottom") and e["entry_side"] in ("top", "bottom"):
                if abs(x1 - x2) < 1.5:
                    pts = [(x1, y1), (x2, y2)]
                else:
                    my = (y1 + y2) / 2.0
                    pts = [(x1, y1), (x1, my), (x2, my), (x2, y2)]
            elif e["exit_side"] in ("left", "right") and e["entry_side"] in ("top", "bottom"):
                pts = [(x1, y1), (x2, y1), (x2, y2)]
            else:
                pts = [(x1, y1), (x1, y2), (x2, y2)]
        clean = [pts[0]]
        for p in pts[1:]:
            if math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 0.5:
                clean.append(p)
        return clean

    def to_svg(self) -> str:
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" style="background:#ffffff;font-family:Arial,Helvetica,sans-serif;">',
            '<defs>',
            '  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">',
            '    <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#555555"/>',
            '  </marker>',
            '  <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">',
            '    <feDropShadow dx="0" dy="1.5" stdDeviation="2" flood-color="#000000" flood-opacity="0.06"/>',
            '  </filter>',
            '</defs>',
            f'<rect width="{self.width}" height="{self.height}" fill="#ffffff"/>',
            f'<text x="{self.width/2}" y="34" text-anchor="middle" font-size="18" font-weight="700" fill="#1e293b">{html.escape(self.title)}</text>',
        ]

        for n in self.nodes:
            if n["kind"] != "zone":
                continue
            fill, stroke = COLORS[n["color"]]
            parts.append(
                f'<rect x="{n["x"]}" y="{n["y"]}" width="{n["w"]}" height="{n["h"]}" rx="10" ry="10" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            )
            align = n.get("align", "left")
            tx = n["x"] + 16 if align == "left" else n["x"] + n["w"] / 2.0
            anchor = "start" if align == "left" else "middle"
            parts.append(
                f'<text x="{tx}" y="{n["y"] + 22}" text-anchor="{anchor}" '
                f'font-size="12.8" font-weight="700" fill="#1e293b">{html.escape(n["label"])}</text>'
            )

        for n in self.nodes:
            if n["kind"] != "box":
                continue
            fill, stroke = COLORS[n["color"]]
            parts.append(
                f'<rect x="{n["x"]}" y="{n["y"]}" width="{n["w"]}" height="{n["h"]}" rx="8" ry="8" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.6" filter="url(#shadow)"/>'
            )
            max_chars_title = max(14, int((n["w"] - 18) / 6.8))
            max_chars_sub = max(16, int((n["w"] - 18) / 5.4))
            title_lines = self._wrap_text(n["title"], max_chars_title)
            sub_lines = self._wrap_text(n["subtitle"], max_chars_sub) if n["subtitle"] else []
            line_h_t = 15.0
            line_h_s = 13.0
            total_h = len(title_lines) * line_h_t + (len(sub_lines) * line_h_s + (5 if sub_lines else 0))
            start_y = n["y"] + (n["h"] - total_h) / 2.0 + 11.5
            cx = n["x"] + n["w"] / 2.0
            for idx, line in enumerate(title_lines):
                parts.append(
                    f'<text x="{cx}" y="{start_y + idx*line_h_t:.1f}" text-anchor="middle" '
                    f'font-size="11.8" font-weight="700" fill="#0f172a">{html.escape(line)}</text>'
                )
            if sub_lines:
                sub_start = start_y + len(title_lines) * line_h_t + 3.0
                for idx, line in enumerate(sub_lines):
                    parts.append(
                        f'<text x="{cx}" y="{sub_start + idx*line_h_s:.1f}" text-anchor="middle" '
                        f'font-size="10.0" font-weight="400" fill="#334155">{html.escape(line)}</text>'
                    )

        for e in self.edges:
            pts = self._compute_orthogonal_pts(e)
            d = self._rounded_orthogonal_path(pts, r=8)
            dash = ' stroke-dasharray="6,4"' if e["dashed"] else ""
            marker_start = ' marker-start="url(#arrow)"' if e["bidir"] else ""
            parts.append(
                f'<path d="{d}" fill="none" stroke="{e["color"]}" stroke-width="2" '
                f'marker-end="url(#arrow)"{marker_start}{dash}/>'
            )

        for e in self.edges:
            if not e["label"]:
                continue
            pts = self._compute_orthogonal_pts(e)
            if e["label_pos"]:
                lx, ly = e["label_pos"]
            else:
                best_seg = max(
                    range(len(pts) - 1),
                    key=lambda i: math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]),
                )
                lx = (pts[best_seg][0] + pts[best_seg + 1][0]) / 2.0
                ly = (pts[best_seg][1] + pts[best_seg + 1][1]) / 2.0
            text_w = len(e["label"]) * 5.7 + 12
            parts.append(
                f'<rect x="{lx - text_w/2:.1f}" y="{ly - 9:.1f}" width="{text_w:.1f}" height="17" '
                f'rx="4" fill="#ffffff" fill-opacity="0.95" stroke="#cbd5e1" stroke-width="0.9"/>'
            )
            parts.append(
                f'<text x="{lx:.1f}" y="{ly + 3.2:.1f}" text-anchor="middle" '
                f'font-size="9.6" font-weight="600" fill="#334155">{html.escape(e["label"])}</text>'
            )

        parts.append("</svg>")
        return "\n".join(parts)


def build_bloc3_architecture() -> DrawioDiagram:
    d = DrawioDiagram(
        "Architecture Pipeline Fraude Bloc 3",
        "Détection de Fraude Bancaire — Architecture Hybride Déployée (Docker + Neon + AWS S3)",
        1420,
        754,
    )

    # Zone 1 : Voie Temps Reel (Docker Local)
    d.add_zone("z_rt", 25, 60, 1370, 326, "1. Voie Temps Réel — Streaming Kafka, Pandera Gate & Inférence FastAPI (Docker Local)")
    # Zone 2 : MLOps, Cloud Manage & Batch Airflow (corridor y=386..452)
    d.add_zone("z_batch", 25, 452, 1370, 232, "2. Gouvernance MLOps, Cloud Managé (Neon + AWS S3) & Orchestration Batch Airflow")

    # Top row inside Zone 1 (y=104, h=96)
    d.add_box("src", 45, 104, 215, 96, "1. Source & Producer", "API Hugging Face / CSV · JSON confluent-kafka (timeout 10s)", "blue")
    d.add_box("kafka", 320, 104, 220, 96, "2. Apache Kafka KRaft (:9092)", "Topics raw-transactions & fraud-dlq · UI :8085", "red")
    d.add_box("pandera", 600, 104, 225, 96, "3. Consumer & Pandera", "Data Quality Gate (amt >= 0, coords GPS valides)", "orange")
    d.add_box("fastapi", 885, 104, 220, 96, "4. FastAPI Scoring (:8080)", "POST /predict · 19.4 ms médiane / 28.9 ms p95", "violet")
    d.add_box("sink", 1165, 104, 210, 96, "5. Alerting & Sink SQL", "PAN **** 1234 · SHA-256 · Mailpit :8025 / Gmail TLS", "green")

    # Quarantine box inside Zone 1 (bottom center under Pandera)
    d.add_box(
        "dlq",
        525,
        260,
        375,
        104,
        "Quarantaine DLQ & Privacy-by-Design (.env)",
        "Rejets amt < 0 / GPS -> topic fraud-dlq + Neon dead_letter_queue + rejected/ (_sanitize_payload_pii)",
        "red",
    )

    # Bottom row inside Zone 2 (y=504, h=144)
    d.add_box(
        "mlflow",
        45,
        504,
        295,
        144,
        "6. MLflow (:5000) + AWS S3 (eu-west-3)",
        "555 719 tx · HistGradientBoosting @champion (0.9876 AUC / 91.61 % Recall) · Bucket S3 21 objets",
        "violet",
    )
    d.add_box(
        "lake",
        380,
        504,
        315,
        144,
        "7. Data Lake Medallion Parquet",
        "bronze/ -> rejected/ -> silver/ (DROP 7 PII + SHA-256 salé) -> gold/ + OpenLineage JSONL",
        "yellow",
    )
    d.add_box(
        "airflow",
        735,
        504,
        295,
        144,
        "8. Apache Airflow 2.11 (:8088)",
        "DAG daily_fraud_audit_pipeline (06h00 UTC) : etl_bronze_to_silver -> gold_audit -> check_retrain",
        "green",
    )
    d.add_box(
        "neon",
        1070,
        504,
        305,
        144,
        "9. Neon PostgreSQL SSL & FinOps",
        "Bases fraud_db & fraud_mlflow_db (eu-central-1) · Hybride ~0,10 €/mois (AWS Full-Cloud : ~30-60 €/mois)",
        "blue",
    )

    # Edges Zone 1 horizontal streaming flow
    d.add_edge("src", "kafka", "produce()", color="#2563eb")
    d.add_edge("kafka", "pandera", "poll()", color="#dc2626")
    d.add_edge("pandera", "fastapi", "Valide", color="#059669")
    d.add_edge("fastapi", "sink", "Score", color="#7c3aed")

    # Pandera -> Quarantaine DLQ
    d.add_edge(
        "pandera", "dlq",
        "amt < 0 -> REJET",
        exit_side="bottom", entry_side="top",
        exit_pos=0.5, entry_pos=0.5,
        color="#dc2626",
        label_pos=(712, 230),
    )

    # Corridor lanes between Zone 1 (y=386) and Zone 2 (y=452): y=401, y=419, y=436
    d.add_edge(
        "mlflow", "fastapi",
        "load @champion (S3)",
        exit_side="top", entry_side="bottom",
        exit_pos=0.5, entry_pos=0.5,
        waypoints=[(192, 401), (995, 401)],
        color="#7c3aed",
        label_pos=(330, 401),
    )
    d.add_edge(
        "dlq", "lake",
        "rejected/",
        exit_side="bottom", entry_side="top",
        exit_pos=0.28, entry_pos=0.5,
        waypoints=[(630, 419), (538, 419)],
        color="#b85450",
        label_pos=(584, 419),
    )
    d.add_edge(
        "dlq", "neon",
        "dead_letter_queue",
        exit_side="bottom", entry_side="top",
        exit_pos=0.72, entry_pos=0.25,
        waypoints=[(795, 419), (1146, 419)],
        dashed=True,
        color="#b85450",
        label_pos=(1075, 419),
    )

    # Sink -> Neon fraud_db (straight down right side) & Medallion bronze/ (lane y=436)
    d.add_edge(
        "sink", "neon",
        "fraud_db (txns + alerts)",
        exit_side="bottom", entry_side="top",
        exit_pos=0.68, entry_pos=0.78,
        color="#059669",
        label_pos=(1298, 305),
    )
    d.add_edge(
        "sink", "lake",
        "Bronze Parquet",
        exit_side="bottom", entry_side="top",
        exit_pos=0.25, entry_pos=0.78,
        waypoints=[(1218, 436), (626, 436)],
        color="#0284c7",
        label_pos=(890, 436),
    )

    # Zone 2 horizontal batch & governance links
    d.add_edge("lake", "airflow", "ETL 06h00", color="#d97706")
    d.add_edge("airflow", "neon", "daily_audit", color="#059669")

    # Bottom highway lanes under Zone 2 (y=704, y=728)
    d.add_edge(
        "airflow", "mlflow",
        "check_retrain (@champion)",
        exit_side="bottom", entry_side="bottom",
        exit_pos=0.5, entry_pos=0.75,
        waypoints=[(882, 704), (266, 704)],
        dashed=True,
        color="#7c3aed",
        label_pos=(574, 704),
    )
    d.add_edge(
        "mlflow", "neon",
        "backend fraud_mlflow_db",
        exit_side="bottom", entry_side="bottom",
        exit_pos=0.25, entry_pos=0.5,
        waypoints=[(119, 728), (1222, 728)],
        dashed=True,
        color="#2563eb",
        label_pos=(670, 728),
    )

    return d


def render_diagram(diag: DrawioDiagram) -> None:
    OUT_DRAWIO.parent.mkdir(parents=True, exist_ok=True)
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    OUT_DRAWIO.write_text(diag.to_drawio_xml(), encoding="utf-8")
    svg = diag.to_svg()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": diag.width, "height": diag.height},
            device_scale_factor=2,
        )
        page.set_content(f"<html><body style='margin:0;padding:0;background:#fff;'>{svg}</body></html>")
        page.screenshot(path=str(OUT_PNG), full_page=True)
        browser.close()
    print(f"[OK] Draw.io : {OUT_DRAWIO} ({OUT_DRAWIO.stat().st_size:,} B)")
    print(f"[OK] PNG 2x  : {OUT_PNG} ({OUT_PNG.stat().st_size:,} B)")


if __name__ == "__main__":
    render_diagram(build_bloc3_architecture())
