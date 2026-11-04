"""Drawing IE7981A01 in the PRICE sheet, matched to the supplied IE7981A01.pdf.

Sheet, BOM, title block and annotations come from the reference (see price_sheet.py and
tools/extract_price_template.py). The view is the real, threaded assembly projected with hidden
lines removed, placed at the reference's position and scale: the manifold's top-left corner at
page point (529.2, 301.3) and 1.3793 pt per model mm (1:2 as printed on A4).
"""
import json
from pathlib import Path

from assembly import vacuum_gripper
from price_sheet import TEMPLATE, BomRow, Sheet, TitleBlock, View, render

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "PDF" / "vacuum_gripper_assembly.pdf"

# Item numbers, part numbers, descriptions and quantities exactly as on the reference BOM.
BOM = [
    BomRow(1, "44665K541", "Standard-Wall Aluminum Pipe Nipple", 1),
    BomRow(2, "5427A612", "Vacuum Cup", 1),
    BomRow(3, "44705K266", "Low-Pressure Aluminum Pipe Fitting", 1),
    BomRow(4, "IE7981P01", "", 1),
    BomRow(5, "5148K143", "High-Pressure D.O.T. Push-to-Connect Fitting", 1),
    BomRow(6, "44665K111", "Standard-Wall Aluminum Pipe Nipple", 1),
]


def build():
    annotations = json.loads((HERE / "ie7981a01_annotations.json").read_text())
    title = TitleBlock(
        drawing_no="IE7981A01",
        description=("SCD", "MC#112", "PARTS REMOVAL TOOL"),
        scale="1:2",
        revision="0",
        sheet="1 of 1",
        size="A",
        drawn_by="OH",
        date_drawn="3/12/2025",
        footer_right="text-to-cad",
        location=TEMPLATE["location"]["text"],
    )
    # Elbow at the left, cup pointing down: the model's +Y is up the page and -Z is to the right.
    view = View(vacuum_gripper().shape, camera=(1, 0, 0), up=(0, 1, 0), k=1.3793,
                anchor_model=(0.0, 48.705 + 9.525, -318.452), anchor_page=(529.2, 301.3))
    return Sheet(title=title, bom=BOM, views=[view], annotations=annotations)


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    render(OUT, build())
    print("wrote", OUT)
