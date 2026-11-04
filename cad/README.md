# Vacuum gripper arm IE7981A01

Built with [text-to-cad](https://github.com/earthtojake/text-to-cad) from the supplied McMaster-Carr
and IE7981P01 STEP files, placed exactly as in the reference assembly
`vendor/IE7981A01_reference_assembly.step` (every part matches its reference bounding box to 0.0000 mm).

| Item | Part | Qty in model |
| --- | --- | --- |
| 1 | 44665K541 pipe nipple, 12 in | 1 |
| 2 | 5427A612 vacuum cup | 1 |
| 3 | 44705K266 pipe elbow, 1/8 NPT female | 1 |
| 4 | IE7981P01 manifold, 3 in x 3/4 in round bar | 1 |
| 5 | 5148K143 push-to-connect elbow | 2 |
| 6 | 44665K111 pipe nipple, 3/4 in | 1 |

```bash
cd cad
cad run src/assembly.py            # build the assembly
cad run src/assembly_drawing.py    # write PDF/vacuum_gripper_assembly.pdf (PRICE sheet, A4, 1:2)
cad export <id> STEP/vacuum_gripper_arm_IE7981A01.step
```

## Drawing (PRICE sheet)

`PDF/vacuum_gripper_assembly.pdf` reproduces the supplied `IE7981A01.pdf` (kept as
`vendor/IE7981A01_reference_drawing.pdf`): same A4 sheet, header strip, BOM, title block, logo,
balloons, weld symbols, notes and product photos, with the real threaded assembly projected with
hidden lines removed at the reference's position and scale.

- `tools/extract_price_template.py` reads the reference PDF and writes `src/price_template.json`
  (frame, header strip, BOM grid, title-block grid, labels, per-glyph text positions),
  `src/ie7981a01_annotations.json` (that drawing's balloons, welds, leaders, notes, photo placement)
  and `assets/` (logo, photos). Run it with pdfplumber and Pillow available.
- `src/price_sheet.py` draws the sheet from that data: Arial / Arial Narrow text metrics, the
  reference's 0.48 / 0.6 pt line weights, BOM rows, title-block fields, footer, rotated location text.
- `src/assembly_drawing.py` fills it in for IE7981A01. BOM quantities and title values are the
  reference's (item 5 shows qty 1 as on the reference; the model contains two).

The first run projects the threaded geometry (about 6 minutes); the result is cached in `.cache/`.

A new drawing needs its own `BomRow` list, `TitleBlock`, `View` (camera, scale, anchor) and, if wanted,
an annotations file (balloons and leaders can be taken from a reference drawing with the extractor).
