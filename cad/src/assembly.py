"""Vacuum gripper arm IE7981A01, built from the vendor parts.

Every component is a vendor part placed with the transform it has in the reference
assembly `vendor/IE7981A01_reference_assembly.step`, so the arrangement is exactly the
supplied design. The manifold is IE7981P01 (`vendor/IE7981P01.step`).

Items: 1 vacuum cup, 2 pipe elbow, 3 12 in nipple, 4 manifold,
       5 push-to-connect elbow (x2), 6 close nipple.
"""
import build123d as bd
from cad import model, read_step

from parts import (VENDOR, manifold, pipe_elbow, pipe_nipple_long, pipe_nipple_short,
                   push_to_connect_elbow, vacuum_cup)

REFERENCE = VENDOR / "IE7981A01_reference_assembly.step"

# (reference component, part model, label)
PLACEMENTS = [
    ("NAUO2", vacuum_cup, "vacuum_cup"),
    ("NAUO3", pipe_elbow, "pipe_elbow"),
    ("NAUO1", pipe_nipple_long, "pipe_nipple_long"),
    ("NAUO4", manifold, "manifold"),
    ("NAUO5", push_to_connect_elbow, "push_to_connect_elbow_upper"),
    ("NAUO6", push_to_connect_elbow, "push_to_connect_elbow_lower"),
    ("NAUO7", pipe_nipple_short, "pipe_nipple_short"),
]


def reference_locations():
    ref = read_step(REFERENCE)
    return {c.label: c.location for c in ref.children}


def placed_parts():
    """[(label, placed shape)] in item order."""
    locs = reference_locations()
    out = []
    for nauo, part, label in PLACEMENTS:
        shape = locs[nauo] * part().shape
        shape.label = label
        out.append((label, shape))
    return out


@model
def vacuum_gripper():
    return bd.Compound(children=[s for _, s in placed_parts()], label="vacuum_gripper")


if __name__ == "__main__":
    vacuum_gripper()
