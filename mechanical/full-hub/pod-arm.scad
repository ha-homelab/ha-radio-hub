// Generated FH1 print part; mm. See parameters.json and physical-fit limits.
difference() {
union() {
cube([31,8,3]);
cube([3,8,13]);
}
translate([-0.1, 4, 8]) { rotate([0, 90, 0]) { cylinder(d=3.3,h=3.2,$fn=48); } }
translate([25, 4, -0.1]) { cylinder(d=2.2,h=3.2,$fn=48); }
}
