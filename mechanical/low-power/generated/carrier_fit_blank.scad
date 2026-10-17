// CONCEPT MOCK-UP ONLY. Units mm. Generated from parameters.json; not a fabrication-ready PCB.
difference() {
cube([160.0,100.0,1.6]);
translate([5.0, 3.5, -0.02]) { cylinder(d=3.4,h=1.6400000000000001,$fn=48); }
translate([155.0, 3.5, -0.02]) { cylinder(d=3.4,h=1.6400000000000001,$fn=48); }
translate([5.0, 95.0, -0.02]) { cylinder(d=3.4,h=1.6400000000000001,$fn=48); }
translate([120.5, 95.0, -0.02]) { cylinder(d=3.4,h=1.6400000000000001,$fn=48); }
}
