// Generated from parameters.json by build.py. Edit parameters.json, then rebuild.
// CSG and STL share the same source. See docs/enclosure.md. Units mm.
difference() {
cube([45.0,36.0,2.0]);
translate([4, 4, -0.02]) { cylinder(d=2.3,h=2.04,$fn=48); }
translate([41.0, 32.0, -0.02]) { cylinder(d=2.3,h=2.04,$fn=48); }
translate([10, 8, -0.02]) { cube([2.5,20.0,2.04]); }
translate([16, 8, -0.02]) { cube([2.5,20.0,2.04]); }
translate([22, 8, -0.02]) { cube([2.5,20.0,2.04]); }
translate([28, 8, -0.02]) { cube([2.5,20.0,2.04]); }
translate([34, 8, -0.02]) { cube([2.5,20.0,2.04]); }
}
