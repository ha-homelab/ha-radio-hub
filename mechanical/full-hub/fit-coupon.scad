// Generated FH1 print part; mm. See parameters.json and physical-fit limits.
difference() {
difference() {
difference() {
difference() {
difference() {
difference() {
difference() {
difference() {
difference() {
difference() {
cube([90,26,5]);
translate([7, 8, -0.1]) { cylinder(d=1.6,h=5.2,$fn=48); }
}
translate([17, 8, -0.1]) { cylinder(d=1.7,h=5.2,$fn=48); }
}
translate([27, 8, -0.1]) { cylinder(d=1.8,h=5.2,$fn=48); }
}
translate([37, 8, -0.1]) { cylinder(d=2.2,h=5.2,$fn=48); }
}
translate([47, 8, -0.1]) { cylinder(d=2.5,h=5.2,$fn=48); }
}
translate([57, 8, -0.1]) { cylinder(d=2.7,h=5.2,$fn=48); }
}
translate([67, 8, -0.1]) { cylinder(d=3.3,h=5.2,$fn=48); }
}
translate([15, 19, -0.1]) { rotate([-90, 0, 0]) { difference() {
rotate([90, 0, 0]) { cylinder(d=6.6,h=5.2,$fn=48); }
translate([-4.3, -6.2, 2.8]) { cube([8.6,7.2,8.6]); }
} } }
}
translate([45, 19, -0.1]) { rotate([-90, 0, 0]) { difference() {
rotate([90, 0, 0]) { cylinder(d=6.8,h=5.2,$fn=48); }
translate([-4.4, -6.2, 2.9]) { cube([8.8,7.2,8.8]); }
} } }
}
translate([75, 19, -0.1]) { rotate([-90, 0, 0]) { difference() {
rotate([90, 0, 0]) { cylinder(d=7.0,h=5.2,$fn=48); }
translate([-4.5, -6.2, 3.0]) { cube([9.0,7.2,9.0]); }
} } }
}
