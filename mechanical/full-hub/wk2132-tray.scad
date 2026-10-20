// Generated FH1 print part; mm. See parameters.json and physical-fit limits.
difference() {
union() {
cube([40.5,35,2.4]);
translate([0, 4, 0]) { cube([2,27,16]); }
translate([38.5, 4, 0]) { cube([2,27,16]); }
}
translate([2, 2, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([38.5, 2, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([2, 33, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([38.5, 33, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([12.15, 2.5, -0.1]) { cube([3,3,2.6]); }
translate([12.15, 29.5, -0.1]) { cube([3,3,2.6]); }
translate([28.349999999999998, 2.5, -0.1]) { cube([3,3,2.6]); }
translate([28.349999999999998, 29.5, -0.1]) { cube([3,3,2.6]); }
translate([-0.1, 6, 5.8]) { cube([4.2,23,20]); }
}
