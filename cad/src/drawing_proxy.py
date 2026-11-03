"""Thread-free stand-ins for the vacuum gripper arm, used only to draw the assembly sheet.

The vendor models carry exact helical threads. Inside their ports those threads only add
hidden-line clutter and degenerate edges to a 2D projection, so the drawing uses these
proxies: male thread zones are cut away, female ports are filled, and the nipples are plain
tubes. Every visible outline is the vendor geometry, placed with the same transforms as
`assembly.vacuum_gripper`.
"""
import build123d as bd

from assembly import reference_locations
from parts import manifold, pipe_elbow, push_to_connect_elbow, vacuum_cup

# Datums measured on the vendor STEP files (mm), in each part's own frame.
ELBOW_PORT_FACE = 8.73125     # pipe_elbow: both port faces
ELBOW_AXIS = -8.73125         # pipe_elbow: leg axes
CUP_SHOULDER_Z = -5.334       # vacuum_cup: hex shoulder face
PTC_SHOULDER_Y = -5.99694     # push_to_connect_elbow: thread shoulder face
PORT_POCKET_RADIUS = 7.0      # clear of the 1/8 NPT thread (major r ~5.2) and the mouth chamfer
PORT_THREAD_DEPTH = 6.8       # female thread length
NIPPLE_R, NIPPLE_BORE_R = 5.144, 3.42


def _solids(part):
    return list(part.solids())


def elbow_proxy():
    """Pipe elbow with each threaded port bored out and filled again with a plain cylinder."""
    solid = _solids(pipe_elbow().shape)[0]
    d = PORT_THREAD_DEPTH
    z_pocket = bd.Pos(0, ELBOW_AXIS, ELBOW_PORT_FACE - d / 2 + 0.5) * bd.Cylinder(PORT_POCKET_RADIUS, d + 1)
    y_pocket = bd.Pos(0, ELBOW_PORT_FACE - d / 2 + 0.5, ELBOW_AXIS) * bd.Rot(X=90) * bd.Cylinder(PORT_POCKET_RADIUS, d + 1)
    z_fill = bd.Pos(0, ELBOW_AXIS, ELBOW_PORT_FACE - d / 2) * bd.Cylinder(PORT_POCKET_RADIUS, d)
    y_fill = bd.Pos(0, ELBOW_PORT_FACE - d / 2, ELBOW_AXIS) * bd.Rot(X=90) * bd.Cylinder(PORT_POCKET_RADIUS, d)
    out = ((solid - z_pocket - y_pocket) + z_fill + y_fill).clean()
    out.label = "pipe_elbow"
    return out


def cup_proxy():
    keep = []
    for s in _solids(vacuum_cup().shape):
        if s.bounding_box().min.Z < CUP_SHOULDER_Z - 1:      # the fitting with the threaded stem
            s = s & (bd.Pos(0, 0, CUP_SHOULDER_Z + 50) * bd.Box(200, 200, 100))
        keep.append(s)
    return bd.Compound(children=keep, label="vacuum_cup")


def ptc_proxy():
    solids = [s for s in _solids(push_to_connect_elbow().shape)
              if s.bounding_box().max.Y > PTC_SHOULDER_Y + 0.1]    # drops thread + sealant ring
    return bd.Compound(children=solids, label="push_to_connect_elbow")


def nipple_proxy(length):
    return bd.Cylinder(NIPPLE_R, length) - bd.Cylinder(NIPPLE_BORE_R, length + 2)


def placed_proxies():
    """{label: proxy shape in assembly coordinates}."""
    loc = reference_locations()
    parts = {
        "vacuum_cup": (loc["NAUO2"], cup_proxy()),
        "pipe_elbow": (loc["NAUO3"], elbow_proxy()),
        "pipe_nipple_long": (loc["NAUO1"], nipple_proxy(304.8)),
        "manifold": (loc["NAUO4"], manifold().shape),
        "push_to_connect_elbow_upper": (loc["NAUO5"], ptc_proxy()),
        "push_to_connect_elbow_lower": (loc["NAUO6"], ptc_proxy()),
        "pipe_nipple_short": (loc["NAUO7"], nipple_proxy(19.05)),
    }
    out = {}
    for label, (location, shape) in parts.items():
        placed = location * shape
        placed.label = label
        out[label] = placed
    return out


def _crop(shape, z_min=None, z_max=None):
    lo = -1e4 if z_min is None else z_min
    hi = 1e4 if z_max is None else z_max
    box = bd.Pos(0, 0, (lo + hi) / 2) * bd.Box(1e3, 1e3, hi - lo)
    out = shape & box
    out.label = shape.label
    return out


def gripper_proxy():
    return bd.Compound(children=list(placed_proxies().values()), label="vacuum_gripper")


def top_detail_proxy():
    """Cup, elbow and the top of the 12 in nipple."""
    p = placed_proxies()
    return bd.Compound(children=[p["vacuum_cup"], p["pipe_elbow"], _crop(p["pipe_nipple_long"], z_min=-40)],
                       label="top_detail")


def bottom_detail_proxy():
    """Bottom of the 12 in nipple, manifold, both push-to-connect elbows and the close nipple."""
    p = placed_proxies()
    return bd.Compound(children=[_crop(p["pipe_nipple_long"], z_max=-305), p["manifold"],
                                 p["push_to_connect_elbow_upper"], p["push_to_connect_elbow_lower"],
                                 p["pipe_nipple_short"]], label="bottom_detail")
