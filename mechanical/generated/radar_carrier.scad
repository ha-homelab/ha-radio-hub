// Generated from parameters.json by build.py. Edit parameters.json, then rebuild.
// CSG and STL share the same source. See docs/enclosure.md. Units mm.
difference() {
cube([84,52,2]);
translate([27, 22, -0.02]) { cube([30,8,2.04]); }
translate([4, 4, -0.02]) { cylinder(d=3.4,h=2.04,$fn=48); }
translate([4, 48, -0.02]) { cylinder(d=3.4,h=2.04,$fn=48); }
translate([80, 4, -0.02]) { cylinder(d=3.4,h=2.04,$fn=48); }
translate([80, 48, -0.02]) { cylinder(d=3.4,h=2.04,$fn=48); }
translate([22, 14, -0.02]) { cube([2,3,2.04]); }
translate([22, 36, -0.02]) { cube([2,3,2.04]); }
translate([58, 14, -0.02]) { cube([2,3,2.04]); }
translate([58, 36, -0.02]) { cube([2,3,2.04]); }
}
