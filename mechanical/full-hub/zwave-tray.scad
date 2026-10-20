// Generated FH1 print part; mm. See parameters.json and physical-fit limits.
difference() {
union() {
cube([36.5,36.5,2.4]);
translate([1, 4, 0]) { cube([2,28.5,20.4]); }
translate([33.5, 4, 0]) { cube([2,28.5,20.4]); }
translate([1, 4, 19.2]) { cube([4,28.5,1.2]); }
translate([31.5, 4, 19.2]) { cube([4,28.5,1.2]); }
}
translate([2, 2, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([34.5, 2, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([2, 34.5, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([34.5, 34.5, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([8, 2.5, -0.1]) { cube([3,3,2.6]); }
translate([8, 31.0, -0.1]) { cube([3,3,2.6]); }
translate([9, 8, -0.1]) { cube([18.5,20.5,2.6]); }
}
