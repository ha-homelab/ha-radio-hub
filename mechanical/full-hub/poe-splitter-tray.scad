// Generated FH1 print part; mm. See parameters.json and physical-fit limits.
difference() {
union() {
cube([110.5,37.6,2.4]);
translate([0, 4, 0]) { cube([2,29.6,16]); }
translate([108.5, 4, 0]) { cube([2,29.6,16]); }
}
translate([2, 2, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([108.5, 2, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([2, 35.6, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([108.5, 35.6, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([33.15, 2.5, -0.1]) { cube([3,3,2.6]); }
translate([33.15, 32.1, -0.1]) { cube([3,3,2.6]); }
translate([77.35, 2.5, -0.1]) { cube([3,3,2.6]); }
translate([77.35, 32.1, -0.1]) { cube([3,3,2.6]); }
translate([-0.1, 6, 5.8]) { cube([4.2,25.6,20]); }
}
