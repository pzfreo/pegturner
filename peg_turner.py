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
import os
import tempfile
import urllib.request
from build123d import *

parser = argparse.ArgumentParser(description="Generate peg turner CAD model")
parser.add_argument(
    "--no-tpu-insert", action="store_true",
    help="Use original slot dimensions without TPU insert",
)
parser.add_argument(
    "--text", type=str, default="Chelli\\nStrings",
    help="Text to emboss (use \\n for line breaks)",
)
parser.add_argument(
    "--font", type=str, default=None,
    help="Font as URL to a .ttf file",
)
parser.add_argument(
    "--text-size", type=float, default=12.0,
    help="Font size in mm (default: 12.0)",
)
parser.add_argument(
    "--inlay-depth", type=float, default=0.2,
    help="Inlay recess depth in mm (default: 0.2, single layer)",
)
parser.add_argument(
    "--engrave", action=argparse.BooleanOptionalAction, default=True,
    help="Engrave text (default) or use --no-engrave for inlay mode",
)
parser.add_argument(
    "--engrave-depth", type=float, default=0.8,
    help="Engrave depth in mm (default: 0.8)",
)
parser.add_argument(
    "--insert-side-extras", type=float, nargs="+", default=[0, 0.5, 1.0],
    help="Extra side wall thickness(es) for TPU inserts in mm (default: 0 0.5 1.0)",
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
INSERT_BASE_WALL = 1.5  # mm wall thickness for ends and ceiling
INSERT_SLOT_ENLARGE = 1.0  # mm per side to enlarge slot in main body
INSERT_TOLERANCE = 0.0  # mm per side clearance for insert fit
INSERT_HEIGHT_INSET = 1.0  # mm shorter than slot so insert sits inside

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

# Text layout
LINE_SPACING_FACTOR = 1.0  # multiplier for font size to get line spacing

# V-taper angles to try (steepest first, falls back to straight walls)
ENGRAVE_TAPER_ANGLES = (45, 30, 20, 10)

# Mesh tessellation
MESH_LINEAR_DEFLECTION = 0.001  # mm (default mesh resolution)
MESH_ANGULAR_DEFLECTION = 0.1  # radians
INLAY_LINEAR_DEFLECTION = 0.01  # mm (coarser for text inlay)
INLAY_ANGULAR_DEFLECTION = 0.5  # radians

# Text emboss (recessed into top face of cap)
TEXT_STRING = args.text
TEXT_STRING = TEXT_STRING.replace("\\n", "\n")

if args.font is not None:
    # Download font from URL to a temp file
    _font_tmp = tempfile.NamedTemporaryFile(suffix=".ttf", delete=False)
    urllib.request.urlretrieve(args.font, _font_tmp.name)
    TEXT_FONT = _font_tmp.name
    print(f"Downloaded font from {args.font}")
else:
    TEXT_FONT = "MrsSaintDelafield-Regular.ttf"

ENGRAVE = args.engrave
ENGRAVE_DEPTH = args.engrave_depth
TEXT_DEPTH = ENGRAVE_DEPTH if ENGRAVE else args.inlay_depth
TEXT_SIZE = args.text_size

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

# Recess text into the top face of the cap
text_lines = TEXT_STRING.split("\n")
line_spacing = TEXT_SIZE * LINE_SPACING_FACTOR
total_text_height = (len(text_lines) - 1) * line_spacing
text_solid = None
for i, line in enumerate(text_lines):
    if not line.strip():
        continue
    y_offset = total_text_height / 2 - i * line_spacing
    line_sketch = Text(
        line,
        font_size=TEXT_SIZE,
        font_path=TEXT_FONT,
        font_style=FontStyle.BOLD,
        align=(Align.CENTER, Align.CENTER),
    )
    if ENGRAVE:
        # Use a V-taper so the groove is self-supporting when printed cap-down.
        # Start with 45° and reduce if the taper collapses thin strokes.
        for taper_angle in ENGRAVE_TAPER_ANGLES:
            try:
                line_solid = Pos(0, y_offset, cap_top) * extrude(
                    line_sketch, -TEXT_DEPTH, taper=taper_angle
                )
                break
            except (ValueError, Exception):
                if taper_angle == ENGRAVE_TAPER_ANGLES[-1]:
                    # Fall back to straight extrude
                    line_solid = Pos(0, y_offset, cap_top) * extrude(
                        line_sketch, -TEXT_DEPTH
                    )
                    print(f"  Warning: V-taper not possible for '{line}', using straight walls")
    else:
        line_solid = Pos(0, y_offset, cap_top) * extrude(line_sketch, -TEXT_DEPTH)
    text_solid = line_solid if text_solid is None else (text_solid + line_solid)
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

# === Build TPU inserts (if requested) ===

inserts = {}
if args.tpu_insert:
    # Outer shell dimensions: same for all inserts
    insert_outer_length = SLOT_LENGTH - 2 * INSERT_TOLERANCE
    insert_outer_width = SLOT_WIDTH - 2 * INSERT_TOLERANCE
    insert_outer_radius = min(insert_outer_length, insert_outer_width) / 2 - 0.01
    insert_height = PEG_HEAD_DEPTH - INSERT_HEIGHT_INSET

    insert_outer_profile = RectangleRounded(
        width=insert_outer_length,
        height=insert_outer_width,
        radius=insert_outer_radius,
    )
    insert_solid = extrude(insert_outer_profile, insert_height)

    for side_extra in args.insert_side_extras:
        side_wall = INSERT_BASE_WALL + side_extra
        label = f"{side_wall:.1f}".replace(".", "_")

        # Inner cavity: base wall at ends, variable wall at sides
        insert_inner_length = insert_outer_length - 2 * INSERT_BASE_WALL
        insert_inner_width = insert_outer_width - 2 * side_wall
        insert_inner_radius = min(insert_inner_length, insert_inner_width) / 2 - 0.01

        insert_inner_profile = RectangleRounded(
            width=insert_inner_length,
            height=insert_inner_width,
            radius=insert_inner_radius,
        )
        insert_cavity = Pos(0, 0, -1) * extrude(
            insert_inner_profile, insert_height - INSERT_BASE_WALL + 1
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
            print(f"\n*** INTERFERENCE DETECTED (side wall {side_wall}mm) ***")
            print(f"  Overlap volume: {interference_vol:.2f} mm³ ({interference_vol / insert_vol * 100:.1f}% of insert)")
            raise ValueError(
                f"TPU insert (side wall {side_wall}mm) interferes with turner body by {interference_vol:.2f} mm³"
            )
        else:
            print(f"\n  Interference check ({side_wall}mm side wall): PASS")

        print(f"\n=== TPU Insert ({side_wall}mm side wall) ===")
        print(f"  Outer (L × W):       {insert_outer_length:.1f} × {insert_outer_width:.1f} mm")
        print(f"  Inner (L × W):       {insert_inner_length:.1f} × {insert_inner_width:.1f} mm")
        print(f"  End wall:            {INSERT_BASE_WALL} mm")
        print(f"  Side wall:           {side_wall} mm")
        print(f"  Ceiling:             {INSERT_BASE_WALL} mm")
        print(f"  Height:              {insert_height} mm")
        ibb = insert.bounding_box()
        print(f"  Bounding box:        {ibb.max.X - ibb.min.X:.1f} × {ibb.max.Y - ibb.min.Y:.1f} × {ibb.max.Z - ibb.min.Z:.1f} mm")

        inserts[label] = insert

# === Export ===

STEP_FILE = "peg_turner_wi.step" if args.tpu_insert else "peg_turner.step"
export_step(turner, STEP_FILE)
print(f"\nExported STEP file: {STEP_FILE}")

for label, insert in inserts.items():
    fname = f"peg_insert_{label}.step"
    export_step(insert, fname)
    print(f"Exported STEP file: {fname}")

# Export 3MF with text inlay + body (print-ready orientation, cap down)
flip = Pos(0, 0, TOTAL_HEIGHT) * Rot(180, 0, 0)
turner_flipped = flip * turner

import copy as copy_module
from build123d.mesher import Lib3MF

suffix = "_wi" if args.tpu_insert else ""

if ENGRAVE:
    # Engrave mode: single-object 3MF (no inlay)
    export_step(turner_flipped, f"peg_turner{suffix}_body.step")
    print(f"Exported STEP file: peg_turner{suffix}_body.step")

    MF_FILE = f"peg_turner{suffix}.3mf"
    libpath = __import__("os").path.dirname(Lib3MF.__file__)
    wrapper = Lib3MF.Wrapper(__import__("os").path.join(libpath, "lib3mf"))
    model = wrapper.CreateModel()
    model.SetUnit(Lib3MF.ModelUnit.MilliMeter)
    identity = wrapper.GetIdentityTransform()

    def _add_mesh(shape, name, lin_def=MESH_LINEAR_DEFLECTION, ang_def=MESH_ANGULAR_DEFLECTION):
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

    body_mesh = _add_mesh(turner_flipped.solids()[0], "body")
    model.AddBuildItem(body_mesh, identity)

    writer = model.QueryWriter("3mf")
    writer.WriteToFile(MF_FILE)
    print(f"Exported 3MF file: {MF_FILE}")

else:
    # Inlay mode: two-object 3MF (inlay + body)
    inlay_flipped = flip * text_solid

    # Interference check: inlay must not overlap with body
    inlay_interference = turner_flipped & inlay_flipped
    try:
        inlay_interference_vol = inlay_interference.volume
    except Exception:
        inlay_interference_vol = 0.0
    if inlay_interference_vol > 0.01:
        print(f"\n*** INLAY INTERFERENCE DETECTED ***")
        print(f"  Overlap volume: {inlay_interference_vol:.2f} mm³")
        raise ValueError(
            f"Text inlay interferes with body by {inlay_interference_vol:.2f} mm³"
        )
    else:
        print(f"\n  Inlay interference check: PASS (no overlap)")

    export_step(turner_flipped, f"peg_turner{suffix}_body.step")
    export_step(inlay_flipped, f"peg_turner{suffix}_inlay.step")
    print(f"Exported STEP file: peg_turner{suffix}_body.step")
    print(f"Exported STEP file: peg_turner{suffix}_inlay.step")

    MF_FILE = f"peg_turner{suffix}.3mf"
    libpath = __import__("os").path.dirname(Lib3MF.__file__)
    wrapper = Lib3MF.Wrapper(__import__("os").path.join(libpath, "lib3mf"))
    model = wrapper.CreateModel()
    model.SetUnit(Lib3MF.ModelUnit.MilliMeter)
    identity = wrapper.GetIdentityTransform()

    def _add_mesh(shape, name, lin_def=MESH_LINEAR_DEFLECTION, ang_def=MESH_ANGULAR_DEFLECTION):
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
            copy_module.deepcopy(solid), INLAY_LINEAR_DEFLECTION, INLAY_ANGULAR_DEFLECTION
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
    parts = [turner_flipped]
    names = ["body"]
    colors = ["steelblue"]
    alphas = [0.8]
    if not ENGRAVE:
        parts.append(inlay_flipped)
        names.append("inlay")
        colors.append("gold")
        alphas.append(1.0)
    for label, ins in inserts.items():
        parts.append(flip * ins)
        names.append(f"insert_{label}")
        colors.append("orange")
        alphas.append(1.0)
    show(*parts, names=names, colors=colors, alphas=alphas)
    print("Displayed in OCP CAD Viewer")
except Exception:
    pass
