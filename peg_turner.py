"""
Peg Turner — 3D CAD model for cello peg turning tool.
See SPEC.md for full design specification.
"""

import math
from build123d import *

# === Parameters ===

# Outer cylinder
OUTER_DIAMETER = 45.0  # mm
OUTER_RADIUS = OUTER_DIAMETER / 2
INTERNAL_DEPTH = 25.0  # mm
END_CAP_THICKNESS = 3.0  # mm
TOTAL_HEIGHT = INTERNAL_DEPTH + END_CAP_THICKNESS  # 28 mm

# Internal slot (peg head socket)
PEG_HEAD_DIAMETER = 28.0  # mm
PEG_HEAD_THICKNESS = 10.0  # mm
TOLERANCE = 0.4  # mm per side for ABS
SLOT_LENGTH = PEG_HEAD_DIAMETER + TOLERANCE  # 28.4 mm
SLOT_WIDTH = PEG_HEAD_THICKNESS + TOLERANCE  # 10.4 mm

# Scallops
NUM_SCALLOPS = 12
SCALLOP_DEPTH = 4.0  # mm

# === Build the peg turner ===

# Start with the outer cylinder
outer = Cylinder(
    radius=OUTER_RADIUS,
    height=TOTAL_HEIGHT,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

# Create the internal slot cavity (open from the top, closed at bottom with end cap)
slot = Box(
    length=SLOT_LENGTH,
    width=SLOT_WIDTH,
    height=INTERNAL_DEPTH + 1,  # +1 to cleanly cut through the open end
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
# Position slot so its bottom sits at the end cap height
slot = Pos(0, 0, END_CAP_THICKNESS) * slot

# Subtract the slot from the cylinder
turner = outer - slot

# Create scallops on the outside
# Each scallop is a cylinder running the full height, positioned at the outer edge
scallop_center_radius = OUTER_RADIUS  # center of scallop circles on the outer edge
scallop_circle_radius = SCALLOP_DEPTH  # radius of each scallop cut

for i in range(NUM_SCALLOPS):
    angle = i * (360.0 / NUM_SCALLOPS)
    angle_rad = math.radians(angle)
    cx = scallop_center_radius * math.cos(angle_rad)
    cy = scallop_center_radius * math.sin(angle_rad)

    scallop = Pos(cx, cy, 0) * Cylinder(
        radius=scallop_circle_radius,
        height=TOTAL_HEIGHT,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    turner = turner - scallop

# === Export ===

STEP_FILE = "peg_turner.step"
export_step(turner, STEP_FILE)
print(f"Exported STEP file: {STEP_FILE}")

# Show in OCP CAD Viewer if active
try:
    from ocp_vscode import show
    show(turner)
    print("Displayed in OCP CAD Viewer")
except Exception:
    pass
