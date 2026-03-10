"""
Peg Turner — 3D CAD model for cello peg turning tool.
See SPEC.md for full design specification.

Mushroom shape: narrow stalk (peg socket) + wide solid cap (scalloped grip).
"""

import math
from build123d import *

# === Parameters ===

# Internal slot (peg head socket)
PEG_HEAD_DIAMETER = 31.0  # mm
PEG_HEAD_THICKNESS = 15.0  # mm
TOLERANCE = 0.4  # mm per side for ABS
SLOT_LENGTH = PEG_HEAD_DIAMETER + TOLERANCE  # 28.4 mm
SLOT_WIDTH = PEG_HEAD_THICKNESS + TOLERANCE  # 10.4 mm

# Stalk (narrow section with slot, stadium shape)
END_WALL_THICKNESS = 3.0  # mm (wall at ends of slot, along length axis)
SIDE_WALL_THICKNESS = 2 * END_WALL_THICKNESS  # mm (wall at sides of slot, along width axis)
STALK_LENGTH = SLOT_LENGTH + 2 * END_WALL_THICKNESS  # derived (outer stadium length)
STALK_WIDTH = SLOT_WIDTH + 2 * SIDE_WALL_THICKNESS  # derived (outer stadium width)
STALK_CORNER_RADIUS = min(STALK_WIDTH, STALK_LENGTH) / 2 - 0.01  # fully rounded ends
PEG_HEAD_DEPTH = 25.0  # mm

# Cap (wide grip section)
CAP_EXTRA_DIAMETER = 10.6  # mm extra beyond stalk max dimension
CAP_DIAMETER = max(STALK_LENGTH, STALK_WIDTH) + CAP_EXTRA_DIAMETER  # derived
CAP_RADIUS = CAP_DIAMETER / 2
CAP_HEIGHT = 10.0  # mm

TOTAL_HEIGHT = PEG_HEAD_DEPTH + CAP_HEIGHT  # 35 mm

# Slot corner rounding
SLOT_CORNER_RADIUS = min(SLOT_WIDTH, SLOT_LENGTH) / 2 - 0.01  # fully rounded ends (stadium shape)

# Fillets
EXTERIOR_FILLET = 2.0  # mm fillet on exterior stalk-to-cap step
INTERIOR_FILLET = 2.0  # mm fillet on interior slot ceiling
STALK_BASE_FILLET = 1.0  # mm fillet on bottom corners of stalk

# Scallops (on cap only)
NUM_SCALLOPS = 12
SCALLOP_DEPTH = 4.0  # mm
SCALLOP_FILLET = 2.0  # mm fillet on scallop edges (matches exterior fillet)

# === Build the peg turner ===

# Stalk: stadium-shaped extrusion, open at bottom
stalk_profile = RectangleRounded(
    width=STALK_LENGTH,
    height=STALK_WIDTH,
    radius=STALK_CORNER_RADIUS,
)
stalk = extrude(stalk_profile, PEG_HEAD_DEPTH)

# Cap: solid wide cylinder sitting on top of stalk
cap = Pos(0, 0, PEG_HEAD_DEPTH) * Cylinder(
    radius=CAP_RADIUS,
    height=CAP_HEIGHT,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

# Combine stalk and cap
turner = stalk + cap

# Fillet the exterior stalk-to-cap junction (on clean geometry, before cuts)
exterior_junction_edges = turner.edges().filter_by(
    lambda e: (
        abs(e.center().Z - PEG_HEAD_DEPTH) < 0.01
        and (e.center().X**2 + e.center().Y**2) > (min(STALK_LENGTH, STALK_WIDTH) / 2) ** 2 * 0.9
    )
)
if exterior_junction_edges:
    turner = fillet(exterior_junction_edges, EXTERIOR_FILLET)

# Fillet the bottom corners of the stalk
stalk_base_edges = turner.edges().filter_by(
    lambda e: (
        abs(e.center().Z) < 0.01
        and (e.center().X**2 + e.center().Y**2) > (min(STALK_LENGTH, STALK_WIDTH) / 2 - 1) ** 2
    )
)
if stalk_base_edges:
    turner = fillet(stalk_base_edges, STALK_BASE_FILLET)

# Create the internal slot cavity with rounded corners (open from the bottom)
slot_profile = RectangleRounded(
    width=SLOT_LENGTH,
    height=SLOT_WIDTH,
    radius=SLOT_CORNER_RADIUS,
)
slot = Pos(0, 0, -1) * extrude(slot_profile, PEG_HEAD_DEPTH + 1)  # extend below to cut cleanly

# Subtract the slot from the turner
turner = turner - slot

# Fillet the interior slot ceiling (where slot meets solid cap)
interior_ceiling_edges = turner.edges().filter_by(
    lambda e: (
        abs(e.center().Z - PEG_HEAD_DEPTH) < 0.5
        and (e.center().X**2 + e.center().Y**2) < (SLOT_LENGTH / 2) ** 2
    )
)
if interior_ceiling_edges:
    turner = fillet(interior_ceiling_edges, INTERIOR_FILLET)

# Create scallops on the cap only
scallop_center_radius = CAP_RADIUS
scallop_circle_radius = SCALLOP_DEPTH

for i in range(NUM_SCALLOPS):
    angle = i * (360.0 / NUM_SCALLOPS)
    angle_rad = math.radians(angle)
    cx = scallop_center_radius * math.cos(angle_rad)
    cy = scallop_center_radius * math.sin(angle_rad)

    scallop = Pos(cx, cy, PEG_HEAD_DEPTH - 1) * Cylinder(
        radius=scallop_circle_radius,
        height=CAP_HEIGHT + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    turner = turner - scallop

# Fillet all scallop edges (top face and vertical edges in one pass)
cap_top = PEG_HEAD_DEPTH + CAP_HEIGHT
inner_radius_sq = (CAP_RADIUS - SCALLOP_DEPTH) ** 2
outer_radius_sq = CAP_RADIUS**2
min_edge_length = CAP_HEIGHT * 0.3
all_scallop_edges = turner.edges().filter_by(
    lambda e: (
        inner_radius_sq * 0.9
        < (e.center().X**2 + e.center().Y**2)
        < outer_radius_sq * 1.1
        and e.center().Z > PEG_HEAD_DEPTH + 0.5
        and e.length > min_edge_length
    )
)
if all_scallop_edges:
    turner = fillet(all_scallop_edges, SCALLOP_FILLET)

# === Print dimensions ===

bb = turner.bounding_box()
print("=== Peg Turner Dimensions ===")
print(f"  Peg head diameter:   {PEG_HEAD_DIAMETER} mm")
print(f"  Peg head thickness:  {PEG_HEAD_THICKNESS} mm")
print(f"  Peg head depth:      {PEG_HEAD_DEPTH} mm")
print(f"  Tolerance:           {TOLERANCE} mm")
print(f"  Slot (L × W):        {SLOT_LENGTH:.1f} × {SLOT_WIDTH:.1f} mm")
print(f"  End wall thickness:  {END_WALL_THICKNESS} mm")
print(f"  Side wall thickness: {SIDE_WALL_THICKNESS} mm")
print(f"  Stalk (L × W):      {STALK_LENGTH:.1f} × {STALK_WIDTH:.1f} mm")
print(f"  Cap diameter:        {CAP_DIAMETER:.1f} mm")
print(f"  Cap height:          {CAP_HEIGHT} mm")
print(f"  Total height:        {TOTAL_HEIGHT:.1f} mm")
print(f"  Scallops:            {NUM_SCALLOPS} × {SCALLOP_DEPTH} mm deep")
print(f"  Scallop fillet:      {SCALLOP_FILLET} mm")
print(f"  Exterior fillet:     {EXTERIOR_FILLET} mm")
print(f"  Interior fillet:     {INTERIOR_FILLET} mm")
print(f"  Stalk base fillet:   {STALK_BASE_FILLET} mm")
print(f"  Bounding box:        {bb.max.X - bb.min.X:.1f} × {bb.max.Y - bb.min.Y:.1f} × {bb.max.Z - bb.min.Z:.1f} mm")

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
