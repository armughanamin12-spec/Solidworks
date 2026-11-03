"""IE7981A01 reference assembly, as supplied (read as-is for comparison)."""
from pathlib import Path

from cad import model, read_step

HERE = Path(__file__).resolve().parent


@model
def reference():
    ref = read_step(HERE.parent / "vendor" / "IE7981A01_reference_assembly.step")
    ref.label = "reference"
    return ref


if __name__ == "__main__":
    reference()
