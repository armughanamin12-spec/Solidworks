# Vacuum gripper assembly

Built with [text-to-cad](https://github.com/earthtojake/text-to-cad) from McMaster-Carr STEP models.

| Item | Part | Thread |
| --- | --- | --- |
| 1 | 44705K266 pipe elbow | 1/8 NPT female x2 (reference part) |
| 2 | 5427A612 vacuum cup | 1/8 NPT male |
| 3 | 5148K143 push-to-connect elbow | 1/8 NPT male |

Both male threads are seated shoulder-to-face in the elbow's ports. The two pipe nipples
(44665K111, 44665K541) are male on both ends, so with no other female part in the set they
are not in the assembly (their STEP files are in `vendor/`).

```bash
cd cad
cad run src/assembly.py            # build the assembly
cad run src/assembly_drawing.py    # write PDF/vacuum_gripper_assembly.pdf (A4, 1:1)
cad export <id> STEP/vacuum_gripper_assembly.step
```

`src/drawing_proxy.py` is a thread-free stand-in used only for the drawing: exact helical
threads produce degenerate edges in the 2D projection.
