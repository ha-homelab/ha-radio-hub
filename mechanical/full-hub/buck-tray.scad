// Generated FH1 print part; mm. See parameters.json and physical-fit limits.
difference() {
union() {
difference() {
union() {
difference() {
union() {
cube([25.8,25.8,2.4]);
translate([0, 4, 0]) { cube([2,17.8,16]); }
translate([23.8, 4, 0]) { cube([2,17.8,16]); }
}
translate([2, 2, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([23.8, 2, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([2, 23.8, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([23.8, 23.8, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([7.74, 2.5, -0.1]) { cube([3,3,2.6]); }
translate([7.74, 20.3, -0.1]) { cube([3,3,2.6]); }
translate([18.06, 2.5, -0.1]) { cube([3,3,2.6]); }
translate([18.06, 20.3, -0.1]) { cube([3,3,2.6]); }
translate([-0.1, 6, 5.8]) { cube([4.2,13.8,20]); }
}
translate([6.3, 19.5, 0]) { cylinder(d=4,h=7.1,$fn=48); }
}
translate([6.3, 19.5, -0.1]) { cylinder(d=1.7,h=7.3,$fn=48); }
}
translate([19.5, 6.3, 0]) { cylinder(d=4,h=7.1,$fn=48); }
}
translate([19.5, 6.3, -0.1]) { cylinder(d=1.7,h=7.3,$fn=48); }
}
