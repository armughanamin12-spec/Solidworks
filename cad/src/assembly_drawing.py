"""Drawing IE7981A01 in the PRICE Industries sheet layout (see price_sheet.py).

Layout and BOM follow the supplied IE7981A01.pdf: one horizontal 1:2 view of the arm, circled
item balloons, BOM table top-left, title block along the bottom. Item numbers and descriptions
are the ones on that drawing.
"""
import numpy as np

from cad import eng_drawing  # noqa: F401  (keeps the server tracking the drawing engine)

from drawing_proxy import placed_proxies
from price_sheet import Balloon, BomRow, TitleBlock, View, render

OUT = "../PDF/vacuum_gripper_assembly.pdf"

# (item, part number, description, labels of the placed parts that count toward the quantity)
BOM = [
    (1, "44665K541", "Standard-Wall Aluminum Pipe Nipple", ("pipe_nipple_long",)),
    (2, "5427A612", "Vacuum Cup", ("vacuum_cup",)),
    (3, "44705K266", "Low-Pressure Aluminum Pipe Fitting", ("pipe_elbow",)),
    (4, "IE7981P01", "", ("manifold",)),
    (5, "5148K143", "High-Pressure D.O.T. Push-to-Connect Fitting",
     ("push_to_connect_elbow_upper", "push_to_connect_elbow_lower")),
    (6, "44665K111", "Standard-Wall Aluminum Pipe Nipple", ("pipe_nipple_short",)),
]


def center(shape):
    c = shape.bounding_box().center()
    return np.array([c.X, c.Y, c.Z])


def build():
    parts = placed_proxies()
    shape = __import__("build123d").Compound(children=list(parts.values()), label="vacuum_gripper")

    bom = [BomRow(item, pn, desc, sum(1 for label in labels if label in parts)) for item, pn, desc, labels in BOM]

    # The arm is drawn lying horizontally, elbow at the left and cup pointing down, as on the
    # reference: the model's +X is toward the viewer and +Y is up the page.
    view = View(shape, camera=(1, 0, 0), up=(0, 1, 0), scale=0.5, center=(132.5, 119.0))

    nipple, manifold, short = center(parts["pipe_nipple_long"]), center(parts["manifold"]), center(parts["pipe_nipple_short"])
    balloons = [
        Balloon("3", target=tuple(center(parts["pipe_elbow"])), at=(46.0, 88.0)),
        Balloon("1", target=(nipple[0], nipple[1], -285.0), at=(165.0, 88.0)),
        Balloon("4", target=(manifold[0], manifold[1] + 6.0, -326.0), at=(199.5, 85.0)),
        Balloon("6", target=(short[0], short[1], -401.0), at=(242.0, 97.0)),
        Balloon("2", target=tuple(center(parts["vacuum_cup"])), at=(46.5, 143.5)),
        Balloon("5", target=tuple(center(parts["push_to_connect_elbow_upper"])), at=(205.0, 138.0)),
        Balloon("5", target=tuple(center(parts["push_to_connect_elbow_lower"])), at=(205.0, 138.0)),
    ]
    title = TitleBlock(
        drawing_no="IE7981A01",
        description=("SCD", "MC#112", "PARTS REMOVAL TOOL"),
        scale="1:2",
        revision="0",
        sheet="1 of 1",
        size="A",
        drawn_by="OH",
        date_drawn="3/12/2025",
    )
    return shape, view, bom, balloons, title


if __name__ == "__main__":
    from pathlib import Path

    shape, view, bom, balloons, title = build()
    out = Path(__file__).resolve().parent / OUT
    render(out.resolve(), [view], bom, balloons, title)
    print("wrote", out.resolve())
