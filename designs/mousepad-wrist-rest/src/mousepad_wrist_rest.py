"""
Gamer-edition integrated wrist-rest mousepad (bilek destekli).

Premium esports silhouette: armor corners, RGB trench, deck rim, hex grip,
cable notch, badge recess, honeycomb underside.

text-to-cad style build123d → STEP/STL for a 250×250 mm FDM tray.
Units: mm. +Z up. Print flat on the bed.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import build123d as bd


@dataclass(frozen=True)
class MousepadParams:
    width: float = 240.0
    depth: float = 240.0
    corner_chamfer: float = 20.0
    corner_fillet: float = 5.5

    pad_thickness: float = 3.8
    rim_height: float = 1.15
    rim_width: float = 2.6

    wrist_depth: float = 76.0
    wrist_front_height: float = 15.0
    wrist_peak_height: float = 20.0
    wrist_peak_y_from_front: float = 28.0
    wrist_blend: float = 36.0
    wrist_side_taper: float = 12.0

    # RGB trench
    rgb_w: float = 1.8
    rgb_d: float = 1.0
    rgb_inset: float = 6.0

    # Hex grip on crest (recessed)
    grip_pitch: float = 8.0
    grip_radius: float = 2.2
    grip_depth: float = 0.65

    cable_w: float = 24.0
    cable_d: float = 9.0
    cable_r: float = 4.5

    badge_w: float = 32.0
    badge_h: float = 11.0
    badge_d: float = 0.8

    # Side tech slots
    slot_len: float = 18.0
    slot_w: float = 2.2
    slot_depth: float = 1.4

    foot_diameter: float = 12.0
    foot_depth: float = 1.2
    foot_inset: float = 20.0

    underside_inset: float = 7.5
    underside_depth: float = 1.5
    hex_pitch: float = 16.0
    hex_inradius: float = 5.5

    def assert_fit(self, bed: float = 250.0, margin_min: float = 2.0) -> None:
        assert self.width <= bed - 2 * margin_min
        assert self.depth <= bed - 2 * margin_min


def _wrist_h(p: MousepadParams, y_from_front: float) -> float:
    peak = p.wrist_peak_y_from_front
    end = p.wrist_depth + p.wrist_blend
    if y_from_front <= 0:
        return p.wrist_front_height
    if y_from_front >= end:
        return p.pad_thickness
    if y_from_front <= peak:
        t = y_from_front / peak
        w = 0.5 - 0.5 * math.cos(math.pi * t)
        return p.wrist_front_height + (p.wrist_peak_height - p.wrist_front_height) * w
    t = (y_from_front - peak) / (end - peak)
    w = t * t * (3 - 2 * t)
    return p.wrist_peak_height + (p.pad_thickness - p.wrist_peak_height) * w


def build_mousepad(p: MousepadParams | None = None) -> bd.Part:
    p = p or MousepadParams()
    p.assert_fit()

    half_w, half_d = p.width / 2, p.depth / 2
    front = -half_d
    end = p.wrist_depth + p.wrist_blend
    c = p.corner_chamfer

    with bd.BuildPart() as part:
        # Armor footprint
        pts = [
            (half_w - c, -half_d),
            (half_w, -half_d + c),
            (half_w, half_d - c),
            (half_w - c, half_d),
            (-half_w + c, half_d),
            (-half_w, half_d - c),
            (-half_w, -half_d + c),
            (-half_w + c, -half_d),
        ]
        with bd.BuildSketch():
            bd.Polygon(*pts)
        bd.extrude(amount=p.wrist_peak_height)
        try:
            bd.fillet(part.edges().filter_by(bd.Axis.Z), p.corner_fillet)
        except Exception:
            pass

        # Wrist height cutter
        samples = 40
        yz = [(front - 4, p.wrist_peak_height + 8), (front - 4, p.wrist_front_height)]
        for i in range(samples + 1):
            y = front + (end / samples) * i
            yz.append((y, _wrist_h(p, y - front)))
        yz += [
            (half_d, p.pad_thickness),
            (half_d + 4, p.pad_thickness),
            (half_d + 4, p.wrist_peak_height + 8),
        ]
        with bd.BuildSketch(bd.Plane.YZ):
            with bd.BuildLine():
                bd.Polyline(*yz, close=True)
            bd.make_face()
        bd.extrude(amount=p.width + 40, both=True, mode=bd.Mode.SUBTRACT)

        # Wing tapers
        for sign in (-1, 1):
            cut_pts = [
                (sign * half_w + sign * 2, front - 2),
                (sign * (half_w - p.wrist_side_taper), front + p.wrist_depth * 0.5),
                (sign * half_w + sign * 2, front + p.wrist_depth + 8),
            ]
            with bd.BuildSketch(bd.Plane.XY.offset(p.pad_thickness + 0.15)):
                bd.Polygon(*cut_pts)
            bd.extrude(amount=p.wrist_peak_height, mode=bd.Mode.SUBTRACT)

        # Front armor bevel (hard-line gamer face)
        with bd.BuildSketch(bd.Plane.XZ.offset(front)):
            bd.Polygon(
                (-half_w + 8, p.wrist_front_height + 0.2),
                (-half_w + 8, p.wrist_peak_height + 2),
                (half_w - 8, p.wrist_peak_height + 2),
                (half_w - 8, p.wrist_front_height + 0.2),
                (half_w - 22, p.wrist_front_height - 2.5),
                (-half_w + 22, p.wrist_front_height - 2.5),
            )
        bd.extrude(amount=6, mode=bd.Mode.SUBTRACT)

        # Deck rim (mouse arena)
        arena_d = half_d - (front + end) - 10
        arena_y = (front + end + 8 + half_d - 6) / 2
        arena_w = p.width - 2 * p.rgb_inset - 4
        if arena_d > 50:
            with bd.Locations((0, arena_y, p.pad_thickness)):
                with bd.BuildSketch():
                    ow, od = arena_w, arena_d
                    bd.RectangleRounded(ow, od, 5)
                    bd.RectangleRounded(
                        ow - 2 * p.rim_width,
                        od - 2 * p.rim_width,
                        3.5,
                        mode=bd.Mode.SUBTRACT,
                    )
                bd.extrude(amount=p.rim_height)

        # RGB trench inside rim
        gd, gw = p.rgb_d, p.rgb_w
        inset = p.rgb_inset
        y0, y1 = front + end + 10, half_d - 7
        if y1 - y0 > 40:
            for sx in (-1, 1):
                with bd.Locations(
                    (sx * (half_w - inset), (y0 + y1) / 2, p.pad_thickness - gd / 2 + 0.05)
                ):
                    bd.Box(gw, y1 - y0 - 4, gd + 0.15, mode=bd.Mode.SUBTRACT)
            with bd.Locations((0, y1, p.pad_thickness - gd / 2 + 0.05)):
                bd.Box(p.width - 2 * inset - 10, gw, gd + 0.15, mode=bd.Mode.SUBTRACT)
            with bd.Locations((0, y0, p.pad_thickness - gd / 2 + 0.05)):
                bd.Box(p.width - 2 * inset - 10, gw, gd + 0.15, mode=bd.Mode.SUBTRACT)

        # Clean hex grip on crest (2 rows)
        crest_y = front + p.wrist_peak_y_from_front
        x0, x1 = -half_w + 26, half_w - 26
        cols = int((x1 - x0) / p.grip_pitch)
        for row in range(2):
            for col in range(cols + 1):
                ox = x0 + col * p.grip_pitch + (row % 2) * (p.grip_pitch * 0.5)
                oy = crest_y - 6 + row * (p.grip_pitch * 0.75)
                if abs(ox) > half_w - 20:
                    continue
                hloc = _wrist_h(p, oy - front)
                with bd.Locations((ox, oy, hloc + 0.05)):
                    with bd.BuildSketch():
                        bd.RegularPolygon(radius=p.grip_radius, side_count=6)
                    bd.extrude(amount=-(p.grip_depth + 0.35), mode=bd.Mode.SUBTRACT)

        # Badge + chevron
        with bd.Locations((0, front + 13, p.wrist_front_height - 0.5)):
            bd.Box(
                p.badge_w,
                p.badge_h,
                p.badge_d + 0.5,
                align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX),
                mode=bd.Mode.SUBTRACT,
            )
        with bd.Locations((0, front + 22, p.wrist_front_height - 1.2)):
            with bd.BuildSketch():
                bd.Polygon((-9, 0), (0, 6), (9, 0), (5.5, 0), (0, 3.5), (-5.5, 0))
            bd.extrude(amount=-(p.badge_d + 0.3), mode=bd.Mode.SUBTRACT)

        # Tech side slots (3 per side, clean)
        for sx in (-1, 1):
            for yy in (front + 48, front + 58, front + 68):
                with bd.Locations((sx * (half_w - 2.0), yy, 9)):
                    bd.Box(
                        p.slot_depth + 2,
                        p.slot_len,
                        p.slot_w,
                        rotation=(0, 0, sx * -8),
                        mode=bd.Mode.SUBTRACT,
                    )

        # Cable notch (rear)
        with bd.Locations((0, half_d, (p.pad_thickness + p.rim_height) / 2)):
            bd.Box(
                p.cable_w,
                p.cable_d * 2,
                p.pad_thickness + p.rim_height + 3,
                mode=bd.Mode.SUBTRACT,
            )
            bd.Cylinder(
                radius=p.cable_r,
                height=p.pad_thickness + p.rim_height + 3,
                mode=bd.Mode.SUBTRACT,
            )

        # Feet
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            with bd.Locations(
                (sx * (half_w - p.foot_inset), sy * (half_d - p.foot_inset), 0)
            ):
                bd.Cylinder(
                    radius=p.foot_diameter / 2,
                    height=p.foot_depth,
                    align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
                    mode=bd.Mode.SUBTRACT,
                )

        # Honeycomb underside (sparser = faster + cleaner)
        pocket_w = p.width - 2 * p.underside_inset
        pocket_d = p.depth - 2 * p.underside_inset
        with bd.Locations((0, 0, 0)):
            bd.Box(
                pocket_w,
                pocket_d,
                p.underside_depth,
                align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
                mode=bd.Mode.SUBTRACT,
            )
        pitch = p.hex_pitch
        R = p.hex_inradius
        y_rows = int(pocket_d / (pitch * 0.866)) + 1
        x_cols = int(pocket_w / pitch) + 1
        for row in range(-y_rows, y_rows + 1):
            for col in range(-x_cols, x_cols + 1):
                cx = col * pitch + (row % 2) * (pitch / 2)
                cy = row * pitch * 0.866
                if abs(cx) > pocket_w / 2 - R - 2:
                    continue
                if abs(cy) > pocket_d / 2 - R - 2:
                    continue
                if cy < front + p.wrist_depth * 0.4:
                    continue
                with bd.Locations((cx, cy, 0)):
                    with bd.BuildSketch():
                        bd.RegularPolygon(radius=R, side_count=6)
                    bd.extrude(amount=p.underside_depth)
        # structural cross
        with bd.Locations((0, 0, 0)):
            bd.Box(3.5, pocket_d, p.underside_depth, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
            bd.Box(pocket_w, 3.5, p.underside_depth, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))

    solid = part.part
    solid.label = "mousepad_wrist_rest_gamer"
    bb = solid.bounding_box()
    assert bb.size.X <= 245.01 and bb.size.Y <= 245.01
    return solid


def export_all(out_dir: Path, p: MousepadParams | None = None) -> dict:
    p = p or MousepadParams()
    out_dir.mkdir(parents=True, exist_ok=True)
    solid = build_mousepad(p)
    bb = solid.bounding_box()
    stl_path = out_dir / "mousepad_wrist_rest.stl"
    step_path = out_dir / "mousepad_wrist_rest.step"
    bd.export_stl(solid, str(stl_path), tolerance=0.05, angular_tolerance=0.12)
    bd.export_step(solid, str(step_path))
    meta = {
        "edition": "gamer",
        "width_mm": round(bb.size.X, 3),
        "depth_mm": round(bb.size.Y, 3),
        "height_mm": round(bb.size.Z, 3),
        "volume_cm3": round(solid.volume / 1000.0, 2),
        "features": [
            "armor_chamfer_corners",
            "rgb_accent_trench",
            "deck_rim",
            "hex_grip",
            "badge_chevron",
            "side_tech_slots",
            "cable_notch",
            "honeycomb_underside",
            "silicone_foot_pockets",
        ],
        "stl": str(stl_path),
        "step": str(step_path),
    }
    (out_dir / "bounds.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    info = export_all(root / "exports")
    print("Built mousepad_wrist_rest (gamer edition)")
    for k, v in info.items():
        print(f"  {k}: {v}")
