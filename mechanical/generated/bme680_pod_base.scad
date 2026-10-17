// Generated from parameters.json by build.py. Edit parameters.json, then rebuild.
// CSG and STL share the same source. See docs/enclosure.md. Units mm.
difference() {
union() {
difference() {
cube([45.0,36.0,18.0]);
translate([2.0, 2.0, 2.0]) { cube([41.0,32.0,20.0]); }
}
translate([4, 4, 0]) { cylinder(d=6,h=18.0,$fn=48); }
translate([41.0, 32.0, 0]) { cylinder(d=6,h=18.0,$fn=48); }
}
translate([4, 4, 10.0]) { cylinder(d=1.8,h=8,$fn=48); }
translate([41.0, 32.0, 10.0]) { cylinder(d=1.8,h=8,$fn=48); }
translate([-0.02, 9, 6]) { cube([2.04,2.5,9]); }
translate([42.98, 9, 6]) { cube([2.04,2.5,9]); }
translate([-0.02, 14, 6]) { cube([2.04,2.5,9]); }
translate([42.98, 14, 6]) { cube([2.04,2.5,9]); }
translate([-0.02, 19, 6]) { cube([2.04,2.5,9]); }
translate([42.98, 19, 6]) { cube([2.04,2.5,9]); }
translate([-0.02, 24, 6]) { cube([2.04,2.5,9]); }
translate([42.98, 24, 6]) { cube([2.04,2.5,9]); }
translate([12, 33.98, 6]) { cube([2.5,2.04,9]); }
translate([18, 33.98, 6]) { cube([2.5,2.04,9]); }
translate([24, 33.98, 6]) { cube([2.5,2.04,9]); }
translate([30, 33.98, 6]) { cube([2.5,2.04,9]); }
translate([20.0, -0.02, 14.0]) { cube([5,2.04,4]); }
translate([12, 18.0, -0.02]) { cube([4,2,2.04]); }
translate([29.0, 18.0, -0.02]) { cube([4,2,2.04]); }
}
