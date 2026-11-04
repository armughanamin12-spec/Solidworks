# Vacuum gripper arm IE7981A01

Built with [text-to-cad](https://github.com/earthtojake/text-to-cad) from the supplied McMaster-Carr
and IE7981P01 STEP files, placed exactly as in the reference assembly
`vendor/IE7981A01_reference_assembly.step` (every part matches its reference bounding box to 0.0000 mm).

| Item | Part | Qty |
| --- | --- | --- |
| 1 | 5427A612 vacuum cup | 1 |
| 2 | 44705K266 pipe elbow, 1/8 NPT female | 1 |
| 3 | 44665K541 pipe nipple, 12 in | 1 |
| 4 | IE7981P01 manifold, 3 in x 3/4 in round bar | 1 |
| 5 | 5148K143 push-to-connect elbow | 2 |
| 6 | 44665K111 pipe nipple, 3/4 in | 1 |

```bash
cd cad
cad run src/assembly.py            # build the assembly
cad run src/assembly_drawing.py    # write PDF/vacuum_gripper_assembly.pdf (PRICE sheet layout, 1:2)
cad export <id> STEP/vacuum_gripper_arm_IE7981A01.step
```

`src/drawing_proxy.py` builds thread-free stand-ins used only for the drawing: exact helical
threads and sub-millimetre fillets produce degenerate edges in the 2D projection. Their
outlines are the vendor geometry. The drawing's views skip hidden lines for the same reason.

## Drawing template

`src/price_sheet.py` reproduces the PRICE Industries sheet from the supplied `IE7981A01.pdf`
(A4 landscape): header strip, BOM table (ITEM NO. / PART NUMBER / DESCRIPTION / QTY),
one hidden-line view with circled balloons and arrowed leaders, full title block, footer.
A new drawing is a script like `src/assembly_drawing.py` that fills in `BomRow`, `View`,
`Balloon` and `TitleBlock` and calls `render(...)`. Quantities are counted from the model.
Item numbers and descriptions follow the reference drawing.
