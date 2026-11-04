"""PRICE Industries drawing sheet (A4 landscape), reproduced from the supplied IE7981A01.pdf.

The sheet is data-driven. `price_template.json` holds the exact geometry of the reference
sheet, extracted from that PDF by `tools/extract_price_template.py`: the header strip, frame,
BOM grid, title-block grid, rounded corners, projection symbols and every static label, in PDF
points from the top-left of the page. `render()` draws that template, fills in the fields
(BOM rows, title block, footer, location), draws the views and the annotations, and writes a
vector PDF.

Text follows the reference: Arial (Liberation Sans, metric-compatible) for the title block,
Arial Narrow (Liberation Sans squeezed to 83%) for the BOM and balloons. Line weights are the
reference's 0.48 pt and 0.6 pt.

A drawing is a script like `assembly_drawing.py` that builds a `Sheet` and calls `render`.
"""
from __future__ import annotations

import datetime
import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import numpy as np

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
CACHE = HERE.parent / ".cache"
TEMPLATE = json.loads((HERE / "price_template.json").read_text())
PAGE_W, PAGE_H = TEMPLATE["page"]

FONT_DIR = Path("/usr/share/fonts/truetype/liberation")
FONT_FILES = {"regular": "LiberationSans-Regular.ttf", "bold": "LiberationSans-Bold.ttf",
              "italic": "LiberationSans-Italic.ttf", "narrow": "LiberationSans-Regular.ttf"}
NARROW = 0.835                      # Arial Narrow / Arial width ratio measured on the reference BOM

# BOM grid of the reference (PDF points). Row boundaries repeat the reference's pitch.
BOM_COLUMNS = [60.8, 117.1, 190.6, 386.0, 442.2]
BOM_ROWS = [46.2, 58.1, 71.4, 84.7, 98.0, 109.9, 123.2, 136.4]
BOM_PITCH = 13.25
BOM_BASELINE = 8.76                 # text baseline below the top of a row
LW_FINE, LW_MEDIUM = 0.48, 0.6

# Reference values of the fields that change from drawing to drawing, used to find their anchors
# in the template. (text, font, size) -> field name.
FIELD_KEYS = {
    ("IE7981A01", "bold", 9.7): "drawing_no", ("1:2", "regular", 6.7): "scale", ("0", "regular", 7.7): "revision",
    ("1 of 1", "regular", 7.7): "sheet", ("OH", "regular", 6.7): "drawn_by", ("3/12/2025", "regular", 6.7): "date_drawn",
    ("SCD", "bold", 6.7): "description_0", ("MC#112", "regular", 6.7): "description_1",
    ("PARTS REMOVAL TOOL", "regular", 6.7): "description_2", ("A", "regular", 6.7): "size",
    ("Solidworks", "regular", 5.8): "footer_right",
}


@dataclass
class BomRow:
    item: int | str
    part_number: str
    description: str
    qty: int | str


@dataclass
class TitleBlock:
    drawing_no: str = ""
    description: Sequence[str] = ()             # up to three lines, the first one bold
    scale: str = "1:2"
    revision: str = "0"
    sheet: str = "1 of 1"
    size: str = "A"
    drawn_by: str = ""
    date_drawn: str = ""
    footer_left: str = ""                       # default: "Print Date: <now> - <drawing no>"
    footer_right: str = ""
    location: str = ""                          # rotated path text along the left edge


@dataclass
class View:
    """An orthographic view of `shape`, drawn with hidden lines removed.

    camera: direction from the part toward the viewer. up: model direction that points up the
    page. `anchor_model` (a model point) is drawn at `anchor_page` (page points from the top-left)
    and `k` is page points per model mm.
    """
    shape: object
    camera: tuple
    up: tuple
    k: float
    anchor_model: tuple
    anchor_page: tuple
    hidden: bool = False
    hidden_shape: object = None     # parts whose hidden (dashed) lines are also drawn, as on the reference


@dataclass
class Sheet:
    title: TitleBlock
    bom: Sequence[BomRow]
    views: Sequence[View] = ()
    annotations: dict = field(default_factory=dict)     # as in ie7981a01_annotations.json


# ---------------------------------------------------------------------------------------
# projection


def _basis(camera, up):
    cam = np.asarray(camera, float)
    forward = -cam / np.linalg.norm(cam)
    right = np.cross(forward, np.asarray(up, float))
    right /= np.linalg.norm(right)
    return right, np.cross(right, forward)


def project_edges(shape, camera, up, hidden=False):
    """Hidden-line projection: ([(visible?, Nx2 polyline)], bbox centre). Coordinates are model mm
    along the view's right/up axes, relative to the shape's bounding-box centre."""
    import build123d as bd
    from build123d import GeomType

    comp = shape if isinstance(shape, bd.Compound) else bd.Compound(children=[shape])
    bb = comp.bounding_box()
    key = (round(bb.min.X, 3), round(bb.min.Y, 3), round(bb.min.Z, 3), round(bb.max.X, 3), round(bb.max.Y, 3),
           round(bb.max.Z, 3), round(comp.volume, 1), tuple(camera), tuple(up), hidden)
    cache_file = CACHE / ("proj2_%x.pkl" % (hash(key) & 0xFFFFFFFF))
    if cache_file.exists():
        return pickle.loads(cache_file.read_bytes())

    c = bb.center()
    cam = np.asarray(camera, float) / np.linalg.norm(camera)
    origin = (c.X + 4000 * cam[0], c.Y + 4000 * cam[1], c.Z + 4000 * cam[2])
    vis, hid = comp.project_to_viewport(origin, viewport_up=tuple(up), look_at=(c.X, c.Y, c.Z))
    out = []
    for is_visible, edges in ((True, vis), (False, hid if hidden else [])):
        for e in edges:
            if e.geom_type == GeomType.LINE:
                pts = [e.start_point(), e.end_point()]
            else:
                n = int(min(160, max(8, e.length / 0.4)))
                pts = e.positions(list(np.linspace(0, 1, n)))
            poly = np.array([[p.X, p.Y] for p in pts])
            if len(poly) == 2 and np.linalg.norm(poly[-1] - poly[0]) < 1e-9:
                continue
            out.append((is_visible, poly))
    result = (out, np.array([c.X, c.Y, c.Z]))
    CACHE.mkdir(exist_ok=True)
    cache_file.write_bytes(pickle.dumps(result))
    return result


def project_point(point, centre, camera, up):
    right, true_up = _basis(camera, up)
    d = np.asarray(point, float) - centre
    return float(d @ right), float(d @ true_up)


# ---------------------------------------------------------------------------------------
# drawing primitives (page points, y measured down from the top; the axes are inverted)


class _Page:
    def __init__(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib import font_manager

        self.plt = plt
        self.fonts = {k: font_manager.FontProperties(fname=str(FONT_DIR / f)) for k, f in FONT_FILES.items()}
        self.fig = plt.figure(figsize=(PAGE_W / 72, PAGE_H / 72))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, PAGE_W)
        self.ax.set_ylim(PAGE_H, 0)
        self.ax.axis("off")

    def line(self, x0, y0, x1, y1, lw):
        self.ax.plot([x0, x1], [y0, y1], color="black", lw=lw, solid_capstyle="butt", zorder=2)

    def poly(self, pts, lw, fill=False, closed=False):
        from matplotlib.patches import Polygon
        pts = np.asarray(pts, float)
        if fill:
            self.ax.add_patch(Polygon(pts, closed=True, fc="black", ec="black", lw=lw, zorder=3))
        else:
            if closed:
                pts = np.vstack([pts, pts[:1]])
            self.ax.plot(pts[:, 0], pts[:, 1], color="black", lw=lw, solid_capstyle="round", zorder=2)

    def circle(self, cx, cy, r, lw):
        from matplotlib.patches import Circle
        self.ax.add_patch(Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=3))

    def text(self, s, x, y, font="regular", size=5.8, ha="left", xs=None):
        """Text with its baseline at y. `ha` is left, center or right about x. With `xs` (glyph
        origins relative to x) every glyph is placed individually, as in the reference."""
        if not s.strip():
            return
        if xs is not None and len(xs) == len(s):
            for ch, dx in zip(s, xs):
                if ch.strip():
                    self.text(ch, x + dx, y, font, size, "left")
            return
        if font == "narrow":
            from matplotlib.patches import PathPatch
            from matplotlib.textpath import TextPath
            from matplotlib.transforms import Affine2D

            tp = TextPath((0, 0), s, size=size, prop=self.fonts["regular"])
            width = (tp.get_extents().x1 if len(tp.vertices) else 0) * NARROW
            x0 = x - {"left": 0, "center": width / 2, "right": width}[ha]
            tr = Affine2D().scale(NARROW, -1).translate(x0, y) + self.ax.transData
            self.ax.add_patch(PathPatch(tp, fc="black", ec="none", transform=tr, zorder=4))
        else:
            self.ax.text(x, y, s, fontproperties=self.fonts[font], fontsize=size, ha=ha, va="baseline", color="black", zorder=4)

    def image(self, path, box):
        from PIL import Image
        img = Image.open(path)
        self.ax.imshow(img, extent=(box[0], box[2], box[3], box[1]), aspect="auto", interpolation="none", zorder=1)
        self.ax.set_xlim(0, PAGE_W)
        self.ax.set_ylim(PAGE_H, 0)


def _eff(font, size):
    """Rendered size: the reference's glyphs measure a little larger than the size its PDF reports."""
    if font == "narrow" or size >= 7:
        return size
    return size * (1.06 if size > 6 else 1.035)


def _field_anchors():
    """{field: text dict} for the template texts that hold per-drawing values, and the static rest."""
    anchors, static = {}, []
    for t in TEMPLATE["texts"]:
        if t["region"] == "bom" and t["y"] > BOM_ROWS[1] - 1:
            continue                                            # BOM data rows are filled in per drawing
        key = (t["text"].strip(), t["font"], round(t["size"], 1))
        name = FIELD_KEYS.get(key)
        if name and name not in anchors:
            anchors[name] = t
            continue
        if t["text"].startswith("Print Date"):
            anchors["footer_left"] = t
            continue
        static.append(t)
    return anchors, static


def _draw_template(page: _Page, sheet: Sheet):
    for x0, y0, x1, y1, lw in TEMPLATE["lines"]:
        page.line(x0, y0, x1, y1, lw)
    for c in TEMPLATE["curves"]:
        page.poly(c["pts"], c["lw"], fill=c["fill"])

    # BOM grid
    rows = list(BOM_ROWS[: len(sheet.bom) + 2])
    while len(rows) < len(sheet.bom) + 2:
        rows.append(rows[-1] + BOM_PITCH)
    for y in rows:
        page.line(BOM_COLUMNS[0], y, BOM_COLUMNS[-1], y, LW_FINE)
    for x in BOM_COLUMNS:
        page.line(x, rows[0], x, rows[-1], LW_FINE)

    anchors, static = _field_anchors()
    for t in static:
        page.text(t["text"], t["x"], t["y"], t["font"], _eff(t["font"], t["size"]), "left", xs=t.get("xs"))

    # BOM text
    mid = [(a + b) / 2 for a, b in zip(BOM_COLUMNS, BOM_COLUMNS[1:])]
    for i, row in enumerate(sheet.bom):
        y = rows[i + 1] + BOM_BASELINE
        page.text(str(row.item), mid[0], y, "narrow", 7.68, "center")
        page.text(row.part_number, BOM_COLUMNS[1] + 1.4, y, "narrow", 7.68, "left")
        page.text(row.description, mid[2], y, "narrow", 7.68, "center")
        page.text(str(row.qty), mid[3], y, "narrow", 7.68, "center")

    # title-block fields, centred where the reference centres them
    t = sheet.title
    now = datetime.datetime.now()
    values = {"drawing_no": t.drawing_no, "scale": t.scale, "revision": t.revision, "sheet": t.sheet, "size": t.size,
              "drawn_by": t.drawn_by, "date_drawn": t.date_drawn, "footer_right": t.footer_right,
              "footer_left": t.footer_left or now.strftime(f"Print Date: %A, %B {now.day}, %Y {now.hour % 12 or 12}:%M:%S %p - ") + t.drawing_no}
    for i, line in enumerate(t.description):
        values[f"description_{i}"] = line
    for name, text in values.items():
        a = anchors.get(name)
        if not a or not text:
            continue
        if name == "footer_left":
            page.text(text, a["x"], a["y"], a["font"], _eff(a["font"], a["size"]), "left")
        elif name == "footer_right":
            page.text(text, a["x1"], a["y"], a["font"], _eff(a["font"], a["size"]), "right")
        else:
            page.text(text, (a["x"] + a["x1"]) / 2, a["y"], a["font"], _eff(a["font"], a["size"]), "center")

    # rotated location text on the left edge
    loc = TEMPLATE["location"]
    if t.location:
        page.ax.text(loc["x"], loc["y"], t.location, fontproperties=page.fonts["regular"], fontsize=loc["size"], rotation=90,
                     rotation_mode="anchor", ha="left", va="baseline", color="black", zorder=4)

    # logo
    page.image(ASSETS / TEMPLATE["logo"]["file"], TEMPLATE["logo"]["box"])


def _draw_annotations(page: _Page, ann: dict):
    for b in ann.get("balloons", []):
        page.circle(b["c"][0], b["c"][1], b["r"], b["lw"])
    for w in ann.get("welds", []):
        page.circle(w["c"][0], w["c"][1], w["r"], w["lw"])
    for x0, y0, x1, y1, lw in ann.get("lines", []):
        page.line(x0, y0, x1, y1, lw)
    for tri in ann.get("arrows", []):
        page.poly(tri, LW_FINE, fill=True)
    for t in ann.get("texts", []):
        page.text(t["text"].strip(), t["x"], t["y"], t["font"], t["size"], "left", xs=t.get("xs"))
    for ph in ann.get("photos", []):
        page.image(ASSETS / ph["file"], ph["box"])


def render(out, sheet: Sheet):
    page = _Page()
    _draw_template(page, sheet)
    for v in sheet.views:
        edges, centre = project_edges(v.shape, v.camera, v.up, hidden=v.hidden)
        ax_, ay_ = project_point(v.anchor_model, centre, v.camera, v.up)
        for visible, poly in edges:
            xs = v.anchor_page[0] + (poly[:, 0] - ax_) * v.k
            ys = v.anchor_page[1] - (poly[:, 1] - ay_) * v.k
            if visible:
                page.ax.plot(xs, ys, color="black", lw=LW_MEDIUM, solid_capstyle="round", zorder=2)
            else:
                page.ax.plot(xs, ys, color="black", lw=LW_FINE, ls=(0, (3, 2)), zorder=2)
        if v.hidden_shape is not None:
            h_edges, h_centre = project_edges(v.hidden_shape, v.camera, v.up, hidden=True)
            hx, hy = project_point(v.anchor_model, h_centre, v.camera, v.up)
            for visible, poly in h_edges:
                if not visible:
                    xs = v.anchor_page[0] + (poly[:, 0] - hx) * v.k
                    ys = v.anchor_page[1] - (poly[:, 1] - hy) * v.k
                    page.ax.plot(xs, ys, color="black", lw=LW_FINE, ls=(0, (3, 2)), zorder=2)
    _draw_annotations(page, sheet.annotations)
    page.fig.savefig(str(out), format="pdf")
    page.plt.close(page.fig)
    return out
