"""Thread-free stand-in for the vacuum gripper, used only to draw the assembly sheet.

The vendor models carry exact helical threads. Inside their ports those threads only
add hidden-line clutter and degenerate edges to a 2D projection, so the drawing uses
this proxy: male thread zones are cut away and the female ports are filled. Every
visible outline is the vendor geometry, placed exactly as in `assembly.vacuum_gripper`.
"""
import build123d as bd

from assembly import (CUP_SHOULDER_Z, ELBOW_AXIS, ELBOW_PORT_FACE, PTC_AXIS_Z,
                      PTC_SHOULDER_Y)
from parts import pipe_elbow, push_to_connect_elbow, vacuum_cup

PORT_POCKET_RADIUS = 7.0   # clear of the 1/8 NPT thread (major radius ~5.2) and the mouth chamfer
PORT_THREAD_DEPTH = 6.8    # female thread length (port face 8.73 down to ~1.9)


def _solids(part):
    return list(part.solids())


def elbow_proxy():
    """Pipe elbow with each threaded port bored out (threads and mouth chamfer, r < 7 mm)
    and filled again with a plain cylinder: same outline, no thread geometry."""
    solid = _solids(pipe_elbow().shape)[0]
    depth = PORT_THREAD_DEPTH
    z_pocket = bd.Pos(0, ELBOW_AXIS, ELBOW_PORT_FACE - depth / 2 + 0.5) * bd.Cylinder(PORT_POCKET_RADIUS, depth + 1)
    y_pocket = (bd.Pos(0, ELBOW_PORT_FACE - depth / 2 + 0.5, ELBOW_AXIS)
                * bd.Rot(X=90) * bd.Cylinder(PORT_POCKET_RADIUS, depth + 1))
    z_fill = bd.Pos(0, ELBOW_AXIS, ELBOW_PORT_FACE - depth / 2) * bd.Cylinder(PORT_POCKET_RADIUS, depth)
    y_fill = (bd.Pos(0, ELBOW_PORT_FACE - depth / 2, ELBOW_AXIS)
              * bd.Rot(X=90) * bd.Cylinder(PORT_POCKET_RADIUS, depth))
    out = ((solid - z_pocket - y_pocket) + z_fill + y_fill).clean()
    out.label = "pipe_elbow"
    return out


def cup_proxy():
    solids = _solids(vacuum_cup().shape)
    keep = []
    for s in solids:
        bb = s.bounding_box()
        if bb.min.Z < CUP_SHOULDER_Z - 1:        # the fitting with the threaded stem
            s = s & (bd.Pos(0, 0, CUP_SHOULDER_Z + 50) * bd.Box(200, 200, 100))
        keep.append(s)
    out = bd.Compound(children=keep, label="vacuum_cup")
    return bd.Pos(0, ELBOW_AXIS, ELBOW_PORT_FACE - CUP_SHOULDER_Z) * out


def ptc_proxy():
    solids = [s for s in _solids(push_to_connect_elbow().shape)
              if s.bounding_box().max.Y > PTC_SHOULDER_Y + 0.1]    # drops thread + sealant ring
    out = bd.Compound(children=solids, label="push_to_connect_elbow")
    return bd.Pos(0, ELBOW_PORT_FACE - PTC_SHOULDER_Y, ELBOW_AXIS - PTC_AXIS_Z) * out


def gripper_proxy():
    return bd.Compound(children=[elbow_proxy(), cup_proxy(), ptc_proxy()], label="vacuum_gripper")
