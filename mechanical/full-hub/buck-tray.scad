// Generated FH1 print part; mm. See parameters.json and physical-fit limits.
difference() {
union() {
union() {
cube([32,32,2.4]);
translate([4, 4, 0]) { cube([2,24,6]); }
translate([26, 4, 0]) { cube([2,24,6]); }
translate([1, 4, 0]) { cube([2,24,9]); }
translate([29, 4, 0]) { cube([2,24,9]); }
translate([4, 2, 0]) { cube([24,1,7]); }
translate([4, 29, 0]) { cube([24,1,7]); }
}
translate([12.5, 29, 0]) { cube([7,3,8]); }
}
translate([2, 2, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([30, 2, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([2, 30, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([30, 30, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([2, 24.5, -0.1]) { cube([2,2.5,12]); }
translate([28, 24.5, -0.1]) { cube([2,2.5,12]); }
translate([12.4, 30.5, 5]) { rotate([0, 90, 0]) { cylinder(d=2.5,h=7.2,$fn=48); } }
}
