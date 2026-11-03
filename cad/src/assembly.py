"""Vacuum cup + pipe elbow + push-to-connect elbow, 1/8 NPT threads seated shoulder-to-face.

The pipe elbow is the reference. It is the only part with female ports, so it takes the
two male-threaded parts. The two pipe nipples are male on both ends and have no female
partner in this set, so they are not part of this assembly.
"""
import build123d as bd
from cad import model

from parts import pipe_elbow, push_to_connect_elbow, vacuum_cup

# Datums measured on the vendor STEP files (mm).
ELBOW_PORT_FACE = 8.73125   # pipe_elbow: both port faces (+Y at y=8.73, +Z at z=8.73)
ELBOW_AXIS = -8.73125       # pipe_elbow: +Z leg axis at y=-8.73125, +Y leg axis at z=-8.73125
CUP_SHOULDER_Z = -5.334     # vacuum_cup: hex shoulder face (thread runs from z=-12.95 up to it)
PTC_SHOULDER_Y = -5.99694   # push_to_connect_elbow: shoulder face of the thread (tip at y=-12.7)
PTC_AXIS_Z = -9.398         # push_to_connect_elbow: thread axis


@model
def vacuum_gripper():
    elbow = pipe_elbow().shape

    # Cup: thread axis onto the elbow's +Z leg, shoulder against the +Z port face.
    cup = bd.Pos(0, ELBOW_AXIS, ELBOW_PORT_FACE - CUP_SHOULDER_Z) * vacuum_cup().shape
    cup.label = "vacuum_cup"

    # Push-to-connect elbow: thread axis onto the +Y leg, shoulder against the +Y port face.
    ptc = bd.Pos(0, ELBOW_PORT_FACE - PTC_SHOULDER_Y, ELBOW_AXIS - PTC_AXIS_Z) * push_to_connect_elbow().shape
    ptc.label = "push_to_connect_elbow"

    return bd.Compound(children=[elbow, cup, ptc], label="vacuum_gripper")


if __name__ == "__main__":
    vacuum_gripper()
