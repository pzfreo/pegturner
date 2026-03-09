# Peg Turner — Design Specification

## Purpose

A cylindrical hand tool that fits over a cello peg head, providing greater leverage to turn sticky pegs.

## Overall Dimensions

| Parameter | Value |
|---|---|
| Outer diameter | 45 mm |
| Internal depth | 25 mm (open end to inner face of cap) |
| End cap thickness | 3 mm |
| Total height | 28 mm |

- **One end open** — for peg insertion
- **One end closed** — flat cap for structural strength

## Internal Socket

The internal cavity is a **slot** shaped to grip the peg head disc:

| Parameter | Value |
|---|---|
| Slot length | 28 mm (matching peg head diameter) |
| Slot width | 10 mm (matching peg head thickness) |
| Slot depth | 25 mm (full internal depth) |
| Tolerance | +0.4 mm on both length and width (ABS clearance) |

**Effective slot dimensions after tolerance: 28.4 mm × 10.4 mm**

Two D-shaped filled sections on either side of the slot prevent the peg head from rotating. The peg head disc slides in through the open end and is gripped along its flat sides.

## External Features

- **12 scallops** evenly spaced around the circumference
- **Scallop depth:** 4 mm (cutting into the 45 mm outer diameter)
- Scallops run the full height of the cylinder

## Manufacturing

| Parameter | Value |
|---|---|
| Process | 3D printing (FDM) |
| Material | ABS |

## Output

- **STEP file** export
- **OCP CAD Viewer** — display model if the viewer is already active; do not attempt to start or stop it; silently handle the case where OCP is not available

## Tech Stack

- **Python** using the **build123d** library
- All parameters organized at the top of the script for easy adjustment
