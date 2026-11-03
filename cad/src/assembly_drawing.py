"""A4 assembly drawing of the vacuum gripper (cup + pipe elbow + push-to-connect elbow)."""
from cad.eng_drawing import Sheet, eng_drawing

from assembly import CUP_SHOULDER_Z, ELBOW_AXIS, ELBOW_PORT_FACE, PTC_AXIS_Z, PTC_SHOULDER_Y
from drawing_proxy import gripper_proxy

# Derived from the assembly's own placements, so the dimensions follow the model.
CUP_DZ = ELBOW_PORT_FACE - CUP_SHOULDER_Z            # cup moved up by this
CUP_TOP_Z = 23.368 + CUP_DZ                          # cup rim (vendor z=23.368)
CUP_RIM_R = 6.99                                     # cup rim radius
PTC_DY = ELBOW_PORT_FACE - PTC_SHOULDER_Y
PTC_DZ = ELBOW_AXIS - PTC_AXIS_Z
TUBE_AXIS_Y = 12.7 + PTC_DY                          # push-in port axis (vendor y=12.7)
CUP_AXIS_Y = ELBOW_AXIS
COLLAR_R = 9.92188                                   # elbow collar radius
COLLAR_MID_Z = 5.5                                   # a z on the +Z leg's collar


@eng_drawing(out="../PDF/vacuum_gripper_assembly.pdf")
def vacuum_gripper_drawing():
    part = gripper_proxy()   # thread-free stand-in; same outline as the assembly
    sheet = Sheet(
        "A4",
        scale=1.0,
        title="VACUUM GRIPPER ASSEMBLY",
        part_number="VG-001",
        material="SEE ITEMS",
        revision="A",
        author="A. AMIN",
        projection="THIRD ANGLE",
        general_tolerance="ISO 2768-m",
        notes=[
            "ITEM 1: PIPE ELBOW, 1/8 NPT FEMALE (MCMASTER 44705K266)",
            "ITEM 2: VACUUM CUP, 1/8 NPT MALE (MCMASTER 5427A612)",
            "ITEM 3: PUSH-TO-CONNECT ELBOW, 1/8 NPT MALE (MCMASTER 5148K143)",
            "THREADS SEATED SHOULDER TO FACE; THREAD DETAIL NOT SHOWN.",
        ],
    )

    # Third angle: the right view sits to the right of the front view, same height.
    front = sheet.view(part, "front", at=(72, 140))
    right = sheet.view(part, "right", at=(168, 140))

    # Front view (X across, Z up): overall width and height.
    front.overall()

    # Right view (Y across, Z up).
    right.dim((0, -18.65313, -18.65313), (0, 34.45, -18.65313 + 1.86), orientation="h")  # overall depth
    right.dim((0, CUP_AXIS_Y, CUP_TOP_Z), (0, TUBE_AXIS_Y, CUP_TOP_Z), orientation="h")  # cup axis to tube axis
    right.dim((0, CUP_AXIS_Y - CUP_RIM_R, ELBOW_PORT_FACE), (0, CUP_AXIS_Y - CUP_RIM_R, CUP_TOP_Z), orientation="v", offset=-14)

    # Item callouts.
    right.note("1", (0, -17.5, -14.0), offset=(-14, -9))
    right.note("2", (0, CUP_AXIS_Y + CUP_RIM_R, CUP_TOP_Z - 3), offset=(14, 4))
    right.note("3", (0, 30.0, -12.0), offset=(10, -10))

    return sheet


if __name__ == "__main__":
    vacuum_gripper_drawing()
