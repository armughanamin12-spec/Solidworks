"""PRICE Industries-style A4 drawing sheet, matched to drawing IE7981A01.

Layout (all in mm, origin top-left of the page, page 297 x 210):
  * header strip: Issued date, Blank qty, Part qty, Factory order no, Completion date,
    Sch date, Comment/Tag, Operator Initials
  * BOM table top-left: ITEM NO. | PART NUMBER | DESCRIPTION | QTY
  * view area: assembly views (hidden-line projected from the model) with circled item
    balloons and arrowed leaders
  * title block along the bottom: ECN, finish, business unit, tolerances, size, material,
    gauge, CNC/tool no, site/description/part-no rows, drawn by / approved by, description,
    drawing no, scale, revision, sheet
  * footer: print date and drawing no, tool name

`render(...)` draws the sheet to a vector PDF. Views are projected here (not by
`cad.eng_drawing`, whose sheet is the ISO layout) with build123d's hidden-line projection.

Typical use (see `assembly_drawing.py`):

    render("out.pdf", views=[View(shape, camera=(1, 0, 0), up=(0, 1, 0), scale=0.5, center=(131, 111))],
           bom=[BomRow(1, "44665K541", "Standard-Wall Aluminum Pipe Nipple", 1), ...],
           balloons=[Balloon("1", target=(x, y, z), at=(165, 88)), ...],
           title=TitleBlock(drawing_no="IE7981A01", ...))
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

PAGE_W, PAGE_H = 297.0, 210.0

# Line weights in points.
LW_FRAME, LW_CELL, LW_VISIBLE, LW_HIDDEN, LW_LEADER = 0.9, 0.5, 0.7, 0.3, 0.5
BALLOON_DIAMETER = 5.2


@dataclass
class BomRow:
    item: int | str
    part_number: str
    description: str
    qty: int | str


@dataclass
class View:
    """An orthographic view of `shape`.

    camera: direction from the part toward the viewer (the view looks along -camera).
    up:     model direction that points up the page.
    center: where the middle of the projected view sits on the sheet, (x, y) in mm from the
            top-left corner.
    """
    shape: object
    camera: tuple
    up: tuple
    scale: float = 0.5
    center: tuple = (150.0, 110.0)
    hidden: bool = False


@dataclass
class Balloon:
    """Circled item number at `at` (sheet mm from top-left) with a leader to model `target`.
    `view` indexes the view the target is projected in."""
    label: str
    target: tuple
    at: tuple
    view: int = 0


@dataclass
class TitleBlock:
    drawing_no: str = ""
    description: Sequence[str] = ()
    scale: str = "1:2"
    revision: str = "0"
    sheet: str = "1 of 1"
    size: str = "A"
    business_unit: str = "PRICE Industries"
    drawn_by: str = ""
    date_drawn: str = ""
    approved_by: str = ""
    date_approved: str = ""
    material: str = ""
    gauge: str = ""
    cnc_tool_no: str = ""
    finish: str = ""
    ecn_desc: str = ""
    ecn_no: str = ""
    tolerance_linear: Sequence[str] = ("X.X", "X.XX", "X.XXX")
    tolerance_unit: str = "INCHES"
    tolerance_angular: str = "X"
    footer_left: str = ""
    footer_right: str = "text-to-cad"


# ---------------------------------------------------------------------------------------
# projection


def _basis(camera, up):
    cam = np.asarray(camera, float)
    cam /= np.linalg.norm(cam)
    forward = -cam
    up = np.asarray(up, float)
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    true_up = np.cross(right, forward)
    return right, true_up


def project_edges(shape, camera, up, hidden=False):
    """[(visible?, Nx2 polyline in model mm centred on the shape's bounding-box centre)]."""
    import build123d as bd

    comp = shape if isinstance(shape, bd.Compound) else bd.Compound(children=[shape])
    c = comp.bounding_box().center()
    cam = np.asarray(camera, float)
    cam = cam / np.linalg.norm(cam)
    origin = (c.X + 4000 * cam[0], c.Y + 4000 * cam[1], c.Z + 4000 * cam[2])
    vis, hid = comp.project_to_viewport(origin, viewport_up=tuple(up), look_at=(c.X, c.Y, c.Z))
    out = []
    for is_visible, edges in ((True, vis), (False, hid if hidden else [])):
        for e in edges:
            if str(e.geom_type).endswith("LINE"):
                pts = [e.start_point(), e.end_point()]
            else:
                n = int(min(160, max(8, e.length / 0.6)))
                pts = e.positions(list(np.linspace(0, 1, n)))
            poly = np.array([[p.X, p.Y] for p in pts])
            if np.linalg.norm(poly[-1] - poly[0]) < 1e-9 and len(poly) == 2:
                continue
            out.append((is_visible, poly))
    return out, np.array([c.X, c.Y, c.Z])


def project_point(point, centre, camera, up):
    right, true_up = _basis(camera, up)
    d = np.asarray(point, float) - centre
    return float(d @ right), float(d @ true_up)


# ---------------------------------------------------------------------------------------
# drawing helpers (coordinates: mm, y measured down from the top of the page)


class _Page:
    def __init__(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        self.plt = plt
        self.fig = plt.figure(figsize=(PAGE_W / 25.4, PAGE_H / 25.4))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, PAGE_W)
        self.ax.set_ylim(0, PAGE_H)
        self.ax.axis("off")

    def y(self, y_top):
        return PAGE_H - y_top

    def rect(self, x0, y0, x1, y1, lw=LW_CELL, rounded=False):
        from matplotlib.patches import FancyBboxPatch, Rectangle
        if rounded:
            p = FancyBboxPatch((x0, self.y(y1)), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=1.4",
                               fill=False, lw=lw, ec="black")
        else:
            p = Rectangle((x0, self.y(y1)), x1 - x0, y1 - y0, fill=False, lw=lw, ec="black")
        self.ax.add_patch(p)

    def line(self, x0, y0, x1, y1, lw=LW_CELL, **kw):
        self.ax.plot([x0, x1], [self.y(y0), self.y(y1)], color="black", lw=lw, solid_capstyle="butt", **kw)

    def text(self, x, y, s, size=6, ha="left", va="center", weight="normal", **kw):
        self.ax.text(x, self.y(y), s, fontsize=size, ha=ha, va=va, fontweight=weight, color="black", **kw)


def _header(page: _Page):
    boxes = [("Issued date", 21.5, 40.2), ("Blank qty", 52.5, 64.8), ("Part qty", 65.0, 75.8),
             ("Factory order no", 77.0, 104.0), ("Completion date", 104.5, 131.0), ("Sch date", 131.6, 143.4),
             ("Comment/Tag", 155.7, 247.0), ("Operator\nInitials", 259.0, 277.8)]
    for label, x0, x1 in boxes:
        page.rect(x0, 7.2, x1, 15.9, lw=LW_CELL, rounded=True)
        page.text(x0 + 1.0, 9.3 if "\n" not in label else 10.0, label, size=4.6, va="center" if "\n" not in label else "center")


def _bom(page: _Page, rows: Sequence[BomRow]):
    x = [21.5, 41.5, 67.8, 137.5, 157.5]
    head_h, row_h, top = 4.0, 4.7, 16.6
    bottom = top + head_h + row_h * len(rows)
    page.rect(x[0], top, x[-1], bottom, lw=LW_CELL)
    for xi in x[1:-1]:
        page.line(xi, top, xi, bottom)
    for j, label in enumerate(("ITEM NO.", "PART NUMBER", "DESCRIPTION", "QTY")):
        page.text((x[j] + x[j + 1]) / 2, top + head_h / 2, label, size=5.6, ha="center")
    for i in range(len(rows) + 1):
        page.line(x[0], top + head_h + i * row_h, x[-1], top + head_h + i * row_h)
    for i, r in enumerate(rows):
        yc = top + head_h + (i + 0.5) * row_h
        page.text((x[0] + x[1]) / 2, yc, str(r.item), size=5.8, ha="center")
        page.text(x[1] + 1.0, yc, r.part_number, size=5.8)
        page.text((x[2] + x[3]) / 2, yc, r.description, size=5.8, ha="center")
        page.text((x[3] + x[4]) / 2, yc, str(r.qty), size=5.8, ha="center")


def _title_block(page: _Page, t: TitleBlock):
    top, bottom = 178.5, 203.0
    xl, xm, xr, x_end = 21.5, 90.4, 184.3, 277.8
    # page frame
    page.rect(21.5, 16.6, x_end, bottom, lw=LW_FRAME)

    # --- left block
    rows = [178.5, 181.6, 184.3, 187.8, 190.4, 193.1, 195.8, bottom]
    page.rect(xl, top, xm, bottom, lw=LW_CELL)
    for yy in rows[1:-1]:
        page.line(xl, yy, xm, yy)
    page.text(xl + 0.8, 180.0, "ECN Desc", size=4.2, weight="bold")
    page.text(xl + 12, 180.0, t.ecn_desc, size=4.2)
    page.text(xl + 0.8, 182.9, "Finish", size=4.2, weight="bold")
    page.text(xl + 12, 182.9, t.finish, size=4.2)
    page.text(xl + 0.8, 186.0, "Business Unit", size=4.2, weight="bold")
    page.text(xl + 33, 186.0, t.business_unit, size=4.6, ha="center")
    page.text((xl + xm) / 2, 189.1, "TOLERANCES UNLESS OTHERWISE SPECIFIED", size=3.9, ha="center", weight="bold")
    # linear row
    cx = [xl, xl + 12.5, xl + 25.5, xl + 38.5, xl + 51.5, xm]
    page.line(cx[1], 190.4, cx[1], 195.8)
    for xi in cx[2:5]:
        page.line(xi, 190.4, xi, 193.1)
    page.line(cx[2], 193.1, cx[2], 195.8)
    page.text(xl + 0.8, 191.8, "LINEAR±", size=4.2, weight="bold")
    for k, v in enumerate(t.tolerance_linear):
        page.text(cx[1] + 1.0 + k * 13.0, 191.8, v, size=4.2)
    page.text(cx[4] + 1.0, 191.8, t.tolerance_unit, size=4.0)
    page.text(xl + 0.8, 194.5, "ANGULAR±", size=4.2, weight="bold")
    page.text(cx[1] + 1.0, 194.5, t.tolerance_angular, size=4.2)
    page.text(cx[2] + 1.0, 194.5, "DEGREES", size=4.0)
    # size / projection / ECN no
    page.line(xl + 14, 195.8, xl + 14, bottom)
    page.line(xl + 36, 195.8, xl + 36, bottom)
    page.text(xl + 0.8, 197.2, "Size", size=4.2, weight="bold")
    page.text(xl + 6, 200.8, t.size, size=6, ha="center")
    _projection_symbol(page, xl + 25, 200.0)
    page.text(xl + 37, 197.2, "Engineering Change No.", size=4.2, weight="bold")
    page.text(xl + 37, 200.8, t.ecn_no, size=5)

    # --- middle block
    page.rect(xm, top, xr, bottom, lw=LW_CELL)
    page.line(xm, 181.5, xr, 181.5)
    page.line(157.5, top, 157.5, 181.5)
    page.line(171.0, top, 171.0, 181.5)
    page.text(xm + 0.8, 180.0, "Material", size=4.2, weight="bold")
    page.text(xm + 12, 180.0, t.material, size=4.6)
    page.text(158.3, 180.0, "Gauge", size=4.2, weight="bold")
    page.text(t.gauge and 163.5 or 163.5, 180.0, t.gauge, size=4.6)
    page.text(171.8, 180.0, "CNC/Tool No.", size=3.9, weight="bold")
    page.text(171.8, 181.0, "", size=3)
    ys = [181.5, 188.7, 195.9, bottom]
    for yy in ys[1:-1]:
        page.line(xm, yy, xr, yy)
    for k in range(3):
        y0 = ys[k]
        page.text(xm + 0.8, y0 + 1.6, "Site", size=4.2, weight="bold")
        page.text(xm + 12, y0 + 2.2, "Description", size=4.2, weight="bold")
        page.text(xm + 12, y0 + 5.4, "Part No", size=4.2, weight="bold", ha="left")
        page.line(xm + 11, y0, xm + 11, ys[k + 1])

    # --- right block
    page.rect(xr, top, x_end, bottom, lw=LW_CELL)
    logo_x1, desc_x0 = 215.0, 215.0
    page.line(desc_x0, top, desc_x0, 194.8)
    page.line(xr, 181.5, desc_x0, 181.5)
    page.text((xr + logo_x1) / 2, 179.8, "PRICE", size=7.5, ha="center", weight="bold", style="italic")
    page.line(xr, 188.7, 215.0, 188.7)
    page.line(xr, 195.9, 215.0, 195.9)
    page.line(198.0, 181.5, 198.0, bottom)
    page.text(xr + 0.8, 183.0, "Drawn by", size=4.2, weight="bold")
    page.text(xr + 6, 186.5, t.drawn_by, size=5, ha="center")
    page.text(198.8, 183.0, "Date Drawn", size=4.2, weight="bold")
    page.text(206.5, 186.5, t.date_drawn, size=5, ha="center")
    page.text(xr + 0.8, 190.2, "Approved By", size=4.2, weight="bold")
    page.text(xr + 6, 193.6, t.approved_by, size=5, ha="center")
    page.text(198.8, 190.2, "Date Approved", size=4.2, weight="bold")
    page.text(206.5, 193.6, t.date_approved, size=5, ha="center")
    # description
    page.text(desc_x0 + 0.8, 180.0, "Description", size=4.2, weight="bold")
    for k, line in enumerate(t.description):
        page.text((desc_x0 + x_end) / 2, 183.2 + k * 3.4, line, size=5.6, ha="center")
    page.line(desc_x0, 194.8, x_end, 194.8)
    page.line(249.6, 194.8, 249.6, bottom)
    page.line(261.1, 194.8, 261.1, bottom)
    page.line(268.3, 194.8, 268.3, bottom)
    page.text(desc_x0 + 0.8, 196.0, "Drawing No.", size=4.2, weight="bold")
    page.text(desc_x0 + 17, 200.6, t.drawing_no, size=9, ha="center", weight="bold")
    page.text(250.4, 196.0, "Scale", size=4.2, weight="bold")
    page.text(255.3, 200.6, t.scale, size=5.4, ha="center")
    page.text(261.9, 196.0, "Revision", size=4.0, weight="bold")
    page.text(264.7, 200.6, t.revision, size=5.4, ha="center")
    page.text(269.0, 196.0, "Sheet", size=4.2, weight="bold")
    page.text(273.0, 200.6, t.sheet, size=5.0, ha="center")

    # footer
    stamp = datetime.date.today().strftime("%A, %B %d, %Y")
    left = t.footer_left or f"Print Date: {stamp} - {t.drawing_no}"
    page.text(21.5, 206.0, left, size=4.6)
    page.text(x_end, 206.0, t.footer_right, size=4.6, ha="right")


def _projection_symbol(page: _Page, x, y):
    """Third-angle projection symbol: a cone seen from the side and end, as in the template."""
    page.line(x - 6, y - 2.6, x - 6, y + 2.6, lw=0.5)
    page.line(x - 6, y - 2.6, x - 1.5, y - 1.2, lw=0.5)
    page.line(x - 6, y + 2.6, x - 1.5, y + 1.2, lw=0.5)
    page.line(x - 1.5, y - 1.2, x - 1.5, y + 1.2, lw=0.5)
    from matplotlib.patches import Circle
    page.ax.add_patch(Circle((x + 4.5, page.y(y)), 2.6, fill=False, lw=0.5, ec="black"))
    page.ax.add_patch(Circle((x + 4.5, page.y(y)), 1.2, fill=False, lw=0.5, ec="black"))


def _balloon(page: _Page, b: Balloon, target_xy):
    from matplotlib.patches import Circle
    bx, by = b.at
    r = BALLOON_DIAMETER / 2
    tx, ty = target_xy
    page.ax.annotate("", xy=(tx, page.y(ty)), xytext=(bx, page.y(by)),
                     arrowprops=dict(arrowstyle="-|>,head_length=0.7,head_width=0.25", lw=LW_LEADER, color="black",
                                     shrinkA=r * 72 / 25.4, shrinkB=0))
    page.ax.add_patch(Circle((bx, page.y(by)), r, fill=True, fc="white", lw=LW_CELL, ec="black", zorder=5))
    page.text(bx, by, b.label, size=6.5, ha="center", zorder=6)


def render(out, views: Sequence[View], bom: Sequence[BomRow], balloons: Sequence[Balloon], title: TitleBlock):
    page = _Page()
    _header(page)
    _bom(page, bom)
    _title_block(page, title)

    projected = []
    for v in views:
        edges, centre = project_edges(v.shape, v.camera, v.up, hidden=v.hidden)
        projected.append((v, edges, centre))
        cx, cy = v.center
        # centre the view's own 2D extent on `center`
        allpts = np.vstack([p for _, p in edges])
        mid = (allpts.min(axis=0) + allpts.max(axis=0)) / 2
        v._offset = mid            # remembered so balloon targets use the same shift
        for visible, poly in edges:
            xs = cx + (poly[:, 0] - mid[0]) * v.scale
            ys = page.y(cy) + (poly[:, 1] - mid[1]) * v.scale
            page.ax.plot(xs, ys, color="black" if visible else "0.45", lw=LW_VISIBLE if visible else LW_HIDDEN,
                         ls="-" if visible else (0, (4, 2)), solid_capstyle="round")

    for b in balloons:
        v, _, centre = projected[b.view]
        px, py = project_point(b.target, centre, v.camera, v.up)
        mid = v._offset
        tx = v.center[0] + (px - mid[0]) * v.scale
        ty = v.center[1] - (py - mid[1]) * v.scale
        _balloon(page, b, (tx, ty))

    page.fig.savefig(str(out), format="pdf")
    page.plt.close(page.fig)
    return out
