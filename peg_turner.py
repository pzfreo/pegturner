"""
Peg Turner — 3D CAD model for cello peg turning tool.
See SPEC.md for full design specification.

Mushroom shape: narrow stalk (peg socket) + wide solid cap (scalloped grip).
"""

import math
from build123d import *

# === Parameters ===

# Stalk (narrow section with slot)
STALK_DIAMETER = 35.0  # mm
STALK_RADIUS = STALK_DIAMETER / 2
STALK_HEIGHT = 25.0  # mm

# Cap (wide grip section)
CAP_DIAMETER = 45.0  # mm
CAP_RADIUS = CAP_DIAMETER / 2
CAP_HEIGHT = 10.0  # mm

TOTAL_HEIGHT = STALK_HEIGHT + CAP_HEIGHT  # 35 mm

# Internal slot (peg head socket, in stalk only)
PEG_HEAD_DIAMETER = 28.0  # mm
PEG_HEAD_THICKNESS = 10.0  # mm
TOLERANCE = 0.4  # mm per side for ABS
SLOT_LENGTH = PEG_HEAD_DIAMETER + TOLERANCE  # 28.4 mm
SLOT_WIDTH = PEG_HEAD_THICKNESS + TOLERANCE  # 10.4 mm

# Slot corner rounding
SLOT_CORNER_RADIUS = min(SLOT_WIDTH, SLOT_LENGTH) / 2 - 0.01  # fully rounded ends (stadium shape)

# Scallops (on cap only)
NUM_SCALLOPS = 12
SCALLOP_DEPTH = 4.0  # mm
SCALLOP_CHAMFER = 0.8  # mm chamfer on scallop edges

# === Build the peg turner ===

# Stalk: narrow cylinder, open at bottom
stalk = Cylinder(
    radius=STALK_RADIUS,
    height=STALK_HEIGHT,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

# Cap: solid wide cylinder sitting on top of stalk
cap = Pos(0, 0, STALK_HEIGHT) * Cylinder(
    radius=CAP_RADIUS,
    height=CAP_HEIGHT,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

# Combine stalk and cap
turner = stalk + cap

# Create the internal slot cavity with rounded corners (open from the bottom)
slot_profile = RectangleRounded(
    width=SLOT_LENGTH,
    height=SLOT_WIDTH,
    radius=SLOT_CORNER_RADIUS,
)
slot = Pos(0, 0, -1) * extrude(slot_profile, STALK_HEIGHT + 1)  # extend below to cut cleanly

# Subtract the slot from the turner
turner = turner - slot

# Create scallops on the cap only
scallop_center_radius = CAP_RADIUS
scallop_circle_radius = SCALLOP_DEPTH

for i in range(NUM_SCALLOPS):
    angle = i * (360.0 / NUM_SCALLOPS)
    angle_rad = math.radians(angle)
    cx = scallop_center_radius * math.cos(angle_rad)
    cy = scallop_center_radius * math.sin(angle_rad)

    scallop = Pos(cx, cy, STALK_HEIGHT) * Cylinder(
        radius=scallop_circle_radius,
        height=CAP_HEIGHT,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    turner = turner - scallop

# Chamfer all sharp edges left by the scallop cuts
inner_radius_sq = (CAP_RADIUS - SCALLOP_DEPTH) ** 2
outer_radius_sq = CAP_RADIUS**2
scallop_edges = turner.edges().filter_by(
    lambda e: (
        inner_radius_sq * 0.9
        < (e.center().X**2 + e.center().Y**2)
        < outer_radius_sq * 1.1
        and e.center().Z >= STALK_HEIGHT - 0.01
    )
)
if scallop_edges:
    turner = chamfer(scallop_edges, SCALLOP_CHAMFER)

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
