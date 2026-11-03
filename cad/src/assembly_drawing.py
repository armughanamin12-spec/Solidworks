"""A4 assembly drawing of the vacuum gripper arm IE7981A01."""
from cad.eng_drawing import Sheet, eng_drawing

from drawing_proxy import bottom_detail_proxy, gripper_proxy, top_detail_proxy

# Model-space facts read off the assembly (mm), used to place dimensions on geometry.
NIPPLE_AXIS_Y = 48.705
CUP_AXIS_Z = -6.35
NIPPLE_TOP_Z, NIPPLE_BOTTOM_Z = -18.7, -323.5            # 12 in nipple (304.8)
MANIFOLD_TOP_Z, MANIFOLD_BOTTOM_Z = -318.452, -394.652   # manifold (76.2)
MANIFOLD_RIGHT_Y, NIPPLE_RIGHT_Y = 58.23, 53.84          # right-hand silhouettes in the right view
MANIFOLD_LEFT_X = -16.8                                  # left-hand silhouette in the front view


@eng_drawing(out="../PDF/vacuum_gripper_assembly.pdf")
def vacuum_gripper_drawing():
    sheet = Sheet(
        "A4",
        scale=0.2,
        title="VACUUM GRIPPER ARM",
        part_number="IE7981A01",
        material="SEE ITEMS",
        revision="A",
        author="A. AMIN",
        projection="THIRD ANGLE",
        general_tolerance="ISO 2768-m",
        notes=[
            "ITEMS: 1 VACUUM CUP 5427A612; 2 PIPE ELBOW 44705K266; 3 NIPPLE 12 IN 44665K541;",
            "4 MANIFOLD IE7981P01; 5 PUSH-TO-CONNECT ELBOW 5148K143 (QTY 2); 6 NIPPLE 3/4 IN 44665K111.",
            "THREADS SEATED; THREAD DETAIL NOT SHOWN.",
        ],
    )

    # Main views at 1:5, third angle: the right view sits right of the front view.
    full = gripper_proxy()
    front = sheet.view(full, "front", at=(32, 132), hidden=False)
    right = sheet.view(full, "right", at=(90, 132), hidden=False)
    front.overall()
    right.overall()
    right.dim((0, NIPPLE_RIGHT_Y, NIPPLE_TOP_Z), (0, NIPPLE_RIGHT_Y, NIPPLE_BOTTOM_Z), orientation="v", offset=10)
    right.dim((0, MANIFOLD_RIGHT_Y, MANIFOLD_TOP_Z), (0, MANIFOLD_RIGHT_Y, MANIFOLD_BOTTOM_Z), orientation="v", offset=18)

    # Detail A: cup end, 1:1 (right view).
    a = sheet.view(top_detail_proxy(), "right", at=(170, 150), scale=1.0, label="DETAIL A (1:1)", hidden=False)
    a.dim((0, 0, 3.57), (0, NIPPLE_AXIS_Y, 3.57), orientation="h")
    a.note("1", (0, 12, CUP_AXIS_Z), offset=(-4, -16))
    a.note("2", (0, 40, -2), offset=(12, 10))
    a.note("3", (0, NIPPLE_AXIS_Y, -33), offset=(14, -6))

    # Detail B: manifold end, 1:2 (front view).
    b = sheet.view(bottom_detail_proxy(), "front", at=(255, 132), scale=0.5, label="DETAIL B (1:2)", hidden=False)
    b.dim((MANIFOLD_LEFT_X, 0, MANIFOLD_TOP_Z), (MANIFOLD_LEFT_X, 0, MANIFOLD_BOTTOM_Z), orientation="v")
    b.note("3", (-7.27, 0, -310), offset=(-14, 6))
    b.note("4", (-7.27, 0, -356), offset=(-14, 0))
    b.note("5", (11.7, 0, -340), offset=(7, 10))
    b.note("5", (11.7, 0, -378), offset=(7, -10))
    b.note("6", (-7.27, 0, -400), offset=(-14, -6))

    return sheet


if __name__ == "__main__":
    vacuum_gripper_drawing()
