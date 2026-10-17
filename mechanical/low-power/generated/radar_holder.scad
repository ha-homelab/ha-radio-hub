// CONCEPT MOCK-UP ONLY. Units mm. Generated from parameters.json; not a fabrication-ready PCB.
difference() {
cube([70.0,38.0,2.0]);
translate([3.0, 3.0, -0.02]) { cylinder(d=3.4,h=2.04,$fn=48); }
translate([3.0, 35.0, -0.02]) { cylinder(d=3.4,h=2.04,$fn=48); }
translate([67.0, 3.0, -0.02]) { cylinder(d=3.4,h=2.04,$fn=48); }
translate([67.0, 35.0, -0.02]) { cylinder(d=3.4,h=2.04,$fn=48); }
translate([10, 8, -0.02]) { cube([2,3,2.04]); }
translate([10, 27.0, -0.02]) { cube([2,3,2.04]); }
translate([58.0, 8, -0.02]) { cube([2,3,2.04]); }
translate([58.0, 27.0, -0.02]) { cube([2,3,2.04]); }
}
