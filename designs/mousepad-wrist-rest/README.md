# Wrist-rest mousepad (bilek destekli)

Parametric integrated wrist-rest mousepad designed for FDM on a **250 × 250 mm** tray.

## Workflow

Follows the [text-to-cad](https://github.com/earthtojake/text-to-cad) approach: a **build123d** Python model builds the solid and exports STEP/STL. An OpenSCAD twin is included for slicer/OpenSCAD users.

```bash
pip install build123d
python3 src/mousepad_wrist_rest.py
```

Outputs land in `exports/` (`mousepad_wrist_rest.stl`, `.step`, `bounds.json`).

## Fit

| Parameter | Value |
| --- | --- |
| Outer footprint | **240 × 240 mm** |
| Peak height | **18.5 mm** |
| Tray | 250 × 250 mm |
| Margin | 5 mm each side |

## Files

- `src/mousepad_wrist_rest.py` — primary parametric source (build123d)
- `src/mousepad_wrist_rest.scad` — OpenSCAD companion
- `exports/` — STL + STEP
- `renders/` — preview PNGs
