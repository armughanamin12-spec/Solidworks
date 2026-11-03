"""McMaster-Carr vendor parts, read from their STEP files as supplied."""
from pathlib import Path

from cad import model, read_step

VENDOR = Path(__file__).resolve().parent.parent / "vendor"


def _vendor(filename, label):
    part = read_step(VENDOR / filename)
    part.label = label
    return part


@model
def vacuum_cup():
    """5427A612: male 1/8 NPT stem on -Z, hex shoulder face at z = -5.33."""
    return _vendor("5427A612_vacuum_cup.step", "vacuum_cup")


@model
def push_to_connect_elbow():
    """5148K143: male 1/8 NPT thread on -Y (axis z = -9.395), tube port on +Z."""
    return _vendor("5148K143_push_to_connect_elbow.step", "push_to_connect_elbow")


@model
def pipe_elbow():
    """44705K266: 90 degree elbow, female 1/8 NPT ports on +Y and +Z (faces at 8.73)."""
    return _vendor("44705K266_pipe_elbow.step", "pipe_elbow")


@model
def pipe_nipple_short():
    """44665K111: 3/4 in close nipple, male 1/8 NPT both ends, along Z."""
    return _vendor("44665K111_pipe_nipple_short.step", "pipe_nipple_short")


@model
def pipe_nipple_long():
    """44665K541: 12 in nipple, male 1/8 NPT both ends, along Z."""
    return _vendor("44665K541_pipe_nipple_long.step", "pipe_nipple_long")


@model
def manifold():
    """IE7981P01: 3 in x 3/4 in round-bar manifold with drilled ports (axis along +X, 0..76.2)."""
    return _vendor("IE7981P01.step", "manifold")


if __name__ == "__main__":
    for m in (vacuum_cup, push_to_connect_elbow, pipe_elbow, pipe_nipple_short, pipe_nipple_long, manifold):
        m()
