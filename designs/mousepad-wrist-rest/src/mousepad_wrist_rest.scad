// Gamer-edition wrist-rest mousepad — OpenSCAD companion (simplified).
// Full-detail source: mousepad_wrist_rest.py (build123d).
// 240×240 mm for 250×250 trays. Units: mm.

width = 240;
depth = 240;
corner_chamfer = 20;
pad_t = 3.8;
wrist_peak = 20;
wrist_front = 15;
wrist_end = 112;
$fn = 48;

module armor_2d() {
  offset(r = 5.5)
    polygon([
      [width/2 - corner_chamfer, -depth/2],
      [width/2, -depth/2 + corner_chamfer],
      [width/2, depth/2 - corner_chamfer],
      [width/2 - corner_chamfer, depth/2],
      [-width/2 + corner_chamfer, depth/2],
      [-width/2, depth/2 - corner_chamfer],
      [-width/2, -depth/2 + corner_chamfer],
      [-width/2 + corner_chamfer, -depth/2]
    ]);
}

function h(yf) =
  yf <= 0 ? wrist_front :
  yf >= wrist_end ? pad_t :
  yf <= 28
    ? let(t = yf/28, w = 0.5 - 0.5*cos(180*t))
      wrist_front + (wrist_peak - wrist_front)*w
    : let(t = (yf-28)/(wrist_end-28), w = t*t*(3-2*t))
      wrist_peak + (pad_t - wrist_peak)*w;

module gamer_mousepad() {
  front = -depth/2;
  difference() {
    linear_extrude(wrist_peak) armor_2d();
    rotate([90,0,90])
      linear_extrude(width+20, center=true)
        polygon(concat(
          [[front-3, wrist_peak+5],[front-3, wrist_front]],
          [for(i=[0:40]) let(y=front+wrist_end*i/40) [y, h(y-front)]],
          [[depth/2, pad_t],[depth/2+3, pad_t],[depth/2+3, wrist_peak+5]]
        ));
    // cable notch
    translate([0, depth/2, pad_t/2]) cube([24, 18, pad_t+4], center=true);
    // RGB trench sample (rear)
    translate([0, depth/2-6, pad_t-0.5]) cube([width-20, 1.8, 1.2], center=true);
  }
}

gamer_mousepad();
