// Parametric integrated wrist-rest mousepad for 250×250 mm FDM trays.
// Companion to the build123d source (text-to-cad style parametric workflow).
// Units: mm. Print flat on the bed (Z up).

/* [Fit] */
width = 240;
depth = 240;
corner_r = 14;
pad_thickness = 3.2;

/* [Wrist rest] */
wrist_front_h = 13;
wrist_peak_h = 18.5;
wrist_peak_from_front = 32;
wrist_end = 100; // peak blend meets pad

/* [Feet / underside] */
foot_d = 12;
foot_depth = 1.2;
foot_inset = 18;
underside_inset = 8;
underside_depth = 1.4;
rib_w = 3;

$fn = 64;

module footprint_2d() {
  offset(r = corner_r)
    square([width - 2 * corner_r, depth - 2 * corner_r], center = true);
}

function wrist_h(y_from_front) =
  y_from_front <= 0 ? wrist_front_h :
  y_from_front >= wrist_end ? pad_thickness :
  y_from_front <= wrist_peak_from_front
    ? let (t = y_from_front / wrist_peak_from_front,
           w = 0.5 - 0.5 * cos(180 * t))
        wrist_front_h + (wrist_peak_h - wrist_front_h) * w
    : let (t = (y_from_front - wrist_peak_from_front) / (wrist_end - wrist_peak_from_front),
           w = 0.5 - 0.5 * cos(180 * t))
        wrist_peak_h + (pad_thickness - wrist_peak_h) * w;

module mousepad() {
  front = -depth / 2;
  samples = 32;
  difference() {
    // blank
    linear_extrude(height = wrist_peak_h)
      footprint_2d();

    // cut above height profile (YZ cutter extruded in X)
    translate([0, 0, 0])
      rotate([90, 0, 90])
        linear_extrude(height = width + 20, center = true)
          polygon(concat(
            [[front - 2, wrist_peak_h + 5], [front - 2, wrist_front_h]],
            [for (i = [0:samples])
              let (y = front + (wrist_end / samples) * i,
                   h = wrist_h(y - front))
              [y, h]
            ],
            [[depth / 2, pad_thickness],
             [depth / 2 + 2, pad_thickness],
             [depth / 2 + 2, wrist_peak_h + 5]]
          ));

    // foot pockets
    for (sx = [-1, 1], sy = [-1, 1])
      translate([sx * (width / 2 - foot_inset), sy * (depth / 2 - foot_inset), -0.01])
        cylinder(d = foot_d, h = foot_depth + 0.01);

    // underside pocket
    translate([0, 0, -0.01])
      cube([width - 2 * underside_inset, depth - 2 * underside_inset, underside_depth + 0.01], center = true);
  }

  // restore cross ribs in underside pocket volume
  translate([0, 0, underside_depth / 2]) {
    cube([rib_w, depth - 2 * underside_inset, underside_depth], center = true);
    cube([width - 2 * underside_inset, rib_w, underside_depth], center = true);
  }
}

mousepad();
