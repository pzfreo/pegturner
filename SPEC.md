# Peg Turner — Design Specification

## Purpose

A cylindrical hand tool that fits over a cello peg head, providing greater leverage to turn sticky pegs. The design uses a mushroom shape — a narrow stalk that fits between adjacent pegs, flaring out to a wider grip cap for leverage.

## Shape Overview

The turner has two sections (mushroom shape):

1. **Stalk** — narrow cylinder containing the peg head socket, fits between adjacent pegs
2. **Cap** — wider solid cylinder with scalloped grip, provides leverage

The peg head inserts from the bottom (open end of the stalk). The cap sits on top, away from the peg box.

## Stalk (Narrow Section)

| Parameter | Value |
|---|---|
| Outer diameter | 35 mm |
| Height | 25 mm |
| Open at bottom | Yes (peg insertion end) |

### Internal Socket

The internal cavity is a **slot** shaped to grip the peg head disc:

| Parameter | Value |
|---|---|
| Slot length | 28 mm (matching peg head diameter) |
| Slot width | 10 mm (matching peg head thickness) |
| Slot depth | 25 mm (full stalk height) |
| Tolerance | +0.4 mm on both length and width (ABS clearance) |
| Corner radius | Fully rounded ends (stadium/oblong shape) |

**Effective slot dimensions after tolerance: 28.4 mm × 10.4 mm**

Two D-shaped filled sections on either side of the slot prevent the peg head from rotating. The peg head disc slides in through the open bottom and is gripped along its flat sides.

Wall thickness is approximately 3 mm on the thin sides of the slot.

## Cap (Grip Section)

| Parameter | Value |
|---|---|
| Outer diameter | 45 mm |
| Height | 10 mm |
| Interior | Solid (no cavity) |
| Transition | Sharp step from stalk |

### External Features

- **12 scallops** evenly spaced around the circumference
- **Scallop depth:** 4 mm (cutting into the 45 mm outer diameter)
- Scallops run the full height of the cap (10 mm)
- All scallop edges chamfered (0.8 mm)

## Overall Dimensions

| Parameter | Value |
|---|---|
| Total height | 35 mm (25 mm stalk + 10 mm cap) |
| Max outer diameter | 45 mm (at cap) |
| Stalk outer diameter | 35 mm |

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
