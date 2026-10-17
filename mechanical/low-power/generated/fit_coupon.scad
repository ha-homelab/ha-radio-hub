// CONCEPT MOCK-UP ONLY. Units mm. Generated from parameters.json; not a fabrication-ready PCB.
difference() {
cube([72,20,8]);
translate([8, 10, -0.02]) { cylinder(d=3.2,h=8.04,$fn=48); }
translate([18, 10, -0.02]) { cylinder(d=3.4,h=8.04,$fn=48); }
translate([28, 10, -0.02]) { cylinder(d=3.6,h=8.04,$fn=48); }
translate([44, 10, 2]) { cylinder(d=4.0,h=6.02,$fn=48); }
translate([54, 10, 2]) { cylinder(d=4.2,h=6.02,$fn=48); }
translate([64, 10, 2]) { cylinder(d=4.4,h=6.02,$fn=48); }
}
