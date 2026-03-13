"""
Peg Turner — 3D CAD model for cello peg turning tool.
See SPEC.md for full design specification.

Mushroom shape: narrow stalk (peg socket) + wide solid cap (scalloped grip).

Usage:
    python peg_turner.py              # Default: enlarged slot + TPU cup insert
    python peg_turner.py --no-tpu-insert # Original design (no insert)
"""

import argparse
import math
from build123d import *

parser = argparse.ArgumentParser(description="Generate peg turner CAD model")
parser.add_argument(
    "--no-tpu-insert", action="store_true",
    help="Use original slot dimensions without TPU insert",
)
args = parser.parse_args()
args.tpu_insert = not args.no_tpu_insert

# === Parameters ===

# Internal slot (peg head socket)
PEG_HEAD_DIAMETER = 31.0  # mm
PEG_HEAD_THICKNESS = 15.0  # mm
TOLERANCE = 0.4  # mm per side for ABS
SLOT_LENGTH_BASE = PEG_HEAD_DIAMETER + TOLERANCE  # 28.4 mm
SLOT_WIDTH_BASE = PEG_HEAD_THICKNESS + TOLERANCE  # 10.4 mm

# TPU insert parameters
INSERT_WALL = 1.5  # mm wall thickness for TPU insert
INSERT_SLOT_ENLARGE = 1.0  # mm per side to enlarge slot in main body
INSERT_TOLERANCE = 0.0  # mm per side clearance for insert fit

if args.tpu_insert:
    SLOT_LENGTH = SLOT_LENGTH_BASE + 2 * INSERT_SLOT_ENLARGE
    SLOT_WIDTH = SLOT_WIDTH_BASE + 2 * INSERT_SLOT_ENLARGE
else:
    SLOT_LENGTH = SLOT_LENGTH_BASE
    SLOT_WIDTH = SLOT_WIDTH_BASE

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

# Text emboss (recessed into top face of cap)
TEXT_STRING = "Chelli"
TEXT_FONT = "MrsSaintDelafield-Regular.ttf"
TEXT_DEPTH = 1.0  # mm recess depth
TEXT_SIZE = 16.0  # mm font size

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

# Fillet the interior slot base (where slot meets stalk bottom opening)
slot_base_edges = turner.edges().filter_by(
    lambda e: (
        abs(e.center().Z) < 0.5
        and (e.center().X**2 + e.center().Y**2) < (SLOT_LENGTH / 2) ** 2
    )
)
if slot_base_edges:
    turner = fillet(slot_base_edges, STALK_BASE_FILLET)

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

# Recess "Chelli" into the top face of the cap
text_sketch = Text(
    TEXT_STRING,
    font_size=TEXT_SIZE,
    font_path=TEXT_FONT,
    font_style=FontStyle.BOLD,
    align=(Align.CENTER, Align.CENTER),
)
text_solid = Pos(0, 0, cap_top) * extrude(text_sketch, -TEXT_DEPTH)
turner = turner - text_solid

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
print(f"  Text size:           {TEXT_SIZE:.1f} mm")
print(f"  Bounding box:        {bb.max.X - bb.min.X:.1f} × {bb.max.Y - bb.min.Y:.1f} × {bb.max.Z - bb.min.Z:.1f} mm")

# === Build TPU insert (if requested) ===

insert = None
if args.tpu_insert:
    # Outer shell: fits inside the enlarged slot (with clearance for glue)
    insert_outer_length = SLOT_LENGTH - 2 * INSERT_TOLERANCE
    insert_outer_width = SLOT_WIDTH - 2 * INSERT_TOLERANCE
    insert_outer_radius = min(insert_outer_length, insert_outer_width) / 2 - 0.01

    # Inner cavity: 2mm wall on each side
    insert_inner_length = insert_outer_length - 2 * INSERT_WALL
    insert_inner_width = insert_outer_width - 2 * INSERT_WALL
    insert_inner_radius = min(insert_inner_length, insert_inner_width) / 2 - 0.01

    INSERT_HEIGHT_INSET = 1.0  # mm shorter than slot so insert sits inside
    insert_height = PEG_HEAD_DEPTH - INSERT_HEIGHT_INSET

    # Outer shell (closed-top cup)
    insert_outer_profile = RectangleRounded(
        width=insert_outer_length,
        height=insert_outer_width,
        radius=insert_outer_radius,
    )
    insert_solid = extrude(insert_outer_profile, insert_height)

    # Inner cavity (open at bottom, closed at top with INSERT_WALL ceiling)
    insert_inner_profile = RectangleRounded(
        width=insert_inner_length,
        height=insert_inner_width,
        radius=insert_inner_radius,
    )
    insert_cavity = Pos(0, 0, -1) * extrude(
        insert_inner_profile, insert_height - INSERT_WALL + 1
    )
    insert = insert_solid - insert_cavity

    # Chamfer the insert outer top edges to clear the slot's interior ceiling fillet
    insert_outer_top_edges = insert.edges().filter_by(
        lambda e: (
            abs(e.center().Z - insert_height) < 0.5
            and (e.center().X**2 + e.center().Y**2)
            > (min(insert_inner_length, insert_inner_width) / 2) ** 2
        )
    )
    if insert_outer_top_edges:
        insert = chamfer(insert_outer_top_edges, INTERIOR_FILLET)

    # Shift insert up so its ceiling is flush with the slot ceiling
    insert = Pos(0, 0, INSERT_HEIGHT_INSET) * insert

    # Interference check: insert must not overlap with turner solid
    interference = turner & insert
    try:
        interference_vol = interference.volume
    except Exception:
        interference_vol = 0.0
    insert_vol = insert.volume
    if interference_vol > 0.01:
        print(f"\n*** INTERFERENCE DETECTED ***")
        print(f"  Overlap volume: {interference_vol:.2f} mm³ ({interference_vol / insert_vol * 100:.1f}% of insert)")
        raise ValueError(
            f"TPU insert interferes with turner body by {interference_vol:.2f} mm³"
        )
    else:
        print(f"\n  Interference check:  PASS (no overlap)")

    print(f"\n=== TPU Insert Dimensions ===")
    print(f"  Outer (L × W):       {insert_outer_length:.1f} × {insert_outer_width:.1f} mm")
    print(f"  Inner (L × W):       {insert_inner_length:.1f} × {insert_inner_width:.1f} mm")
    print(f"  Wall thickness:      {INSERT_WALL} mm")
    print(f"  Height:              {insert_height} mm")
    ibb = insert.bounding_box()
    print(f"  Bounding box:        {ibb.max.X - ibb.min.X:.1f} × {ibb.max.Y - ibb.min.Y:.1f} × {ibb.max.Z - ibb.min.Z:.1f} mm")

# === Export ===

STEP_FILE = "peg_turner_wi.step" if args.tpu_insert else "peg_turner.step"
export_step(turner, STEP_FILE)
print(f"\nExported STEP file: {STEP_FILE}")

if insert is not None:
    INSERT_STEP_FILE = "peg_insert.step"
    export_step(insert, INSERT_STEP_FILE)
    print(f"Exported STEP file: {INSERT_STEP_FILE}")

# Export 3MF with text inlay + body (print-ready orientation, cap down)
flip = Pos(0, 0, TOTAL_HEIGHT) * Rot(180, 0, 0)
turner_flipped = flip * turner

inlay_flipped = flip * text_solid

suffix = "_wi" if args.tpu_insert else ""
export_step(turner_flipped, f"peg_turner{suffix}_body.step")
export_step(inlay_flipped, f"peg_turner{suffix}_inlay.step")
print(f"Exported STEP file: peg_turner{suffix}_body.step")
print(f"Exported STEP file: peg_turner{suffix}_inlay.step")

# Export 3MF with exactly two parts: inlay + body
import copy as copy_module
from build123d.mesher import Lib3MF

MF_FILE = f"peg_turner{suffix}.3mf"
libpath = __import__("os").path.dirname(Lib3MF.__file__)
wrapper = Lib3MF.Wrapper(__import__("os").path.join(libpath, "lib3mf"))
model = wrapper.CreateModel()
model.SetUnit(Lib3MF.ModelUnit.MilliMeter)
identity = wrapper.GetIdentityTransform()


def _add_mesh(shape, name, lin_def=0.001, ang_def=0.1):
    """Tessellate a single Shape and add it as one mesh object."""
    verts, tris = Mesher._mesh_shape(
        copy_module.deepcopy(shape), lin_def, ang_def
    )
    if len(verts) < 3 or not tris:
        return None
    v3mf, t3mf = Mesher._create_3mf_mesh(verts, tris)
    mesh = model.AddMeshObject()
    mesh.SetGeometry(v3mf, t3mf)
    mesh.SetType(Lib3MF.ObjectType.Model)
    mesh.SetName(name)
    return mesh


# Tessellate all inlay solids and merge into a single mesh
all_verts = []
all_tris = []
vert_offset = 0
for solid in inlay_flipped.solids():
    verts, tris = Mesher._mesh_shape(
        copy_module.deepcopy(solid), 0.01, 0.5
    )
    if len(verts) < 3 or not tris:
        continue
    all_verts.extend(verts)
    all_tris.extend((a + vert_offset, b + vert_offset, c + vert_offset)
                     for a, b, c in tris)
    vert_offset += len(verts)

v3mf, t3mf = Mesher._create_3mf_mesh(all_verts, all_tris)
inlay_mesh = model.AddMeshObject()
inlay_mesh.SetGeometry(v3mf, t3mf)
inlay_mesh.SetType(Lib3MF.ObjectType.Model)
inlay_mesh.SetName("inlay")
model.AddBuildItem(inlay_mesh, identity)

# Tessellate body as a single mesh
body_mesh = _add_mesh(turner_flipped.solids()[0], "body")
model.AddBuildItem(body_mesh, identity)

writer = model.QueryWriter("3mf")
writer.WriteToFile(MF_FILE)
print(f"Exported 3MF file: {MF_FILE}")

# Show in OCP CAD Viewer if active
try:
    from ocp_vscode import show
    parts = [turner_flipped, inlay_flipped]
    names = ["body", "inlay"]
    colors = ["steelblue", "gold"]
    alphas = [0.8, 1.0]
    if insert is not None:
        parts.append(insert)
        names.append("insert")
        colors.append("orange")
        alphas.append(1.0)
    show(*parts, names=names, colors=colors, alphas=alphas)
    print("Displayed in OCP CAD Viewer")
except Exception:
    pass
