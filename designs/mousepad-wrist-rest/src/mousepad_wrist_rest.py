"""
Parametric integrated wrist-rest mousepad (bilek destekli mousepad).

Adapted from the text-to-cad workflow: a build123d Python model that exports
STEP/STL for FDM on a 250 × 250 mm tray (outer footprint ≤ ~245 × 245 mm).

Units: millimetres. +Z up. Flat on the bed for printing (no supports intended).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import build123d as bd


@dataclass(frozen=True)
class MousepadParams:
    # Hard fit: 250×250 mm tray → leave 2–5 mm margin each side
    width: float = 240.0
    depth: float = 240.0
    corner_radius: float = 14.0

    # Thin usable mouse deck
    pad_thickness: float = 3.2

    # Wrist rest (user / front edge at Y = -depth/2)
    wrist_depth: float = 72.0
    wrist_front_height: float = 13.0
    wrist_peak_height: float = 18.5
    wrist_peak_y_from_front: float = 32.0
    wrist_blend: float = 28.0  # distance after peak where height meets pad

    # Soft top edge on the rest
    top_fillet: float = 4.0
    deck_edge_fillet: float = 1.2

    # Adhesive silicone foot pockets (optional retail finish)
    foot_diameter: float = 12.0
    foot_depth: float = 1.2
    foot_inset: float = 18.0

    # Underside lightening (keeps outer rim solid for stability)
    underside_inset: float = 8.0
    underside_depth: float = 1.4
    rib_width: float = 3.0

    @property
    def max_xy(self) -> float:
        return max(self.width, self.depth)

    def assert_fit(self, bed: float = 250.0, margin_min: float = 2.0) -> None:
        assert self.width <= bed - 2 * margin_min
        assert self.depth <= bed - 2 * margin_min
        assert self.corner_radius * 2 < min(self.width, self.depth)
        assert self.wrist_depth + self.wrist_blend < self.depth - 40.0
        assert self.wrist_peak_height > self.pad_thickness + 5.0


def _wrist_heights(p: MousepadParams, y_from_front: float) -> float:
    """Smooth height profile from front edge along +Y (depth)."""
    import math

    peak = p.wrist_peak_y_from_front
    end = p.wrist_depth + p.wrist_blend
    if y_from_front <= 0:
        return p.wrist_front_height
    if y_from_front >= end:
        return p.pad_thickness

    # Piecewise cosine blends: front→peak, peak→pad
    if y_from_front <= peak:
        t = y_from_front / peak
        w = 0.5 - 0.5 * math.cos(math.pi * t)
        return p.wrist_front_height + (p.wrist_peak_height - p.wrist_front_height) * w

    t = (y_from_front - peak) / (end - peak)
    w = 0.5 - 0.5 * math.cos(math.pi * t)
    return p.wrist_peak_height + (p.pad_thickness - p.wrist_peak_height) * w


def build_mousepad(p: MousepadParams | None = None) -> bd.Part:
    import math

    p = p or MousepadParams()
    p.assert_fit()

    half_w = p.width / 2
    half_d = p.depth / 2
    front = -half_d

    # Sample the side-profile polyline (Y,Z) then extrude in X and clip to footprint
    samples = 28
    end = p.wrist_depth + p.wrist_blend
    ys = [front + (end / samples) * i for i in range(samples + 1)]
    # Continue flat pad to back edge
    ys.append(half_d)

    # Build a solid by lofting thin cross-section slices (YZ profiles) along X is heavy;
    # instead: revolve-free approach — extrude rounded footprint to max height, then
    # cut away the volume above the wrist/pad height field with a swept cutter.

    with bd.BuildPart() as part:
        # Outer blank
        with bd.BuildSketch():
            bd.RectangleRounded(p.width, p.depth, p.corner_radius)
        bd.extrude(amount=p.wrist_peak_height)

        # Cut the upper cavity so the top surface follows the height profile.
        # Build a cutting prism in the YZ plane extruded across X (oversized).
        profile_pts: list[bd.Vector] = []
        # Start below origin so the cutter clears the front face
        profile_pts.append(bd.Vector(0, front - 2, p.wrist_peak_height + 5))
        profile_pts.append(bd.Vector(0, front - 2, p.wrist_front_height))

        for y in ys:
            yff = y - front
            h = _wrist_heights(p, yff) if y <= front + end else p.pad_thickness
            # Slight clamp near back
            if y >= half_d:
                h = p.pad_thickness
            profile_pts.append(bd.Vector(0, y, h))

        profile_pts.append(bd.Vector(0, half_d + 2, p.pad_thickness))
        profile_pts.append(bd.Vector(0, half_d + 2, p.wrist_peak_height + 5))

        yz_pts = [(pt.Y, pt.Z) for pt in profile_pts]
        with bd.BuildSketch(bd.Plane.YZ) as cutter_sk:
            with bd.BuildLine():
                bd.Polyline(*yz_pts, close=True)
            bd.make_face()
        bd.extrude(amount=p.width + 20, both=True, mode=bd.Mode.SUBTRACT)

        # Foot pockets on the underside (print bed face = Z=0)
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            fx = sx * (half_w - p.foot_inset)
            fy = sy * (half_d - p.foot_inset)
            with bd.Locations((fx, fy, 0)):
                bd.Cylinder(
                    radius=p.foot_diameter / 2,
                    height=p.foot_depth,
                    align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
                    mode=bd.Mode.SUBTRACT,
                )

        # Underside lightening pocket with cross ribs (keeps rim + feet solid)
        pocket_w = p.width - 2 * p.underside_inset
        pocket_d = p.depth - 2 * p.underside_inset
        if pocket_w > 20 and pocket_d > 20 and p.underside_depth > 0:
            with bd.Locations((0, 0, 0)):
                bd.Box(
                    pocket_w,
                    pocket_d,
                    p.underside_depth,
                    align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
                    mode=bd.Mode.SUBTRACT,
                )
            # Restore cross ribs
            with bd.Locations((0, 0, 0)):
                bd.Box(
                    p.rib_width,
                    pocket_d,
                    p.underside_depth,
                    align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
                )
                bd.Box(
                    pocket_w,
                    p.rib_width,
                    p.underside_depth,
                    align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
                )

        # Soften top perimeter where accessible (deck + rest crest)
        # Filleting the entire top wire can fail on complex topology; fillet the
        # longest top edges selectively.
        try:
            top_edges = [
                e
                for e in part.edges().filter_by(bd.GeomType.CIRCLE)
                if abs(e.center().Z - p.pad_thickness) < 0.4
                or abs(e.center().Z - p.wrist_peak_height) < 0.6
            ]
            # Also include long line edges near the pad top
            for e in part.edges().filter_by(bd.GeomType.LINE):
                z = e.center().Z
                if abs(z - p.pad_thickness) < 0.35 and e.length > 20:
                    top_edges.append(e)
            if top_edges:
                bd.fillet(top_edges, p.deck_edge_fillet)
        except Exception:
            # Geometry still valid without cosmetic fillets
            pass

    solid = part.part
    solid.label = "mousepad_wrist_rest"

    bb = solid.bounding_box()
    assert bb.size.X <= 245.0 + 1e-6, f"width {bb.size.X} exceeds 245 mm"
    assert bb.size.Y <= 245.0 + 1e-6, f"depth {bb.size.Y} exceeds 245 mm"
    assert bb.size.X <= 250.0 and bb.size.Y <= 250.0
    # Peak height should stay near design intent
    assert bb.size.Z <= p.wrist_peak_height + 1.0

    return solid


def export_all(out_dir: Path, p: MousepadParams | None = None) -> dict:
    p = p or MousepadParams()
    out_dir.mkdir(parents=True, exist_ok=True)
    solid = build_mousepad(p)
    bb = solid.bounding_box()

    stl_path = out_dir / "mousepad_wrist_rest.stl"
    step_path = out_dir / "mousepad_wrist_rest.step"
    bd.export_stl(solid, str(stl_path), tolerance=0.08, angular_tolerance=0.2)
    bd.export_step(solid, str(step_path))

    meta = {
        "width_mm": round(bb.size.X, 3),
        "depth_mm": round(bb.size.Y, 3),
        "height_mm": round(bb.size.Z, 3),
        "volume_cm3": round(solid.volume / 1000.0, 2),
        "stl": str(stl_path),
        "step": str(step_path),
    }
    (out_dir / "bounds.json").write_text(
        __import__("json").dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    return meta


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    info = export_all(root / "exports")
    print("Built mousepad_wrist_rest")
    for k, v in info.items():
        print(f"  {k}: {v}")
